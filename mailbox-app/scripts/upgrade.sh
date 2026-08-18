#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

usage() {
  cat >&2 <<'EOF'
Usage:
  sudo /opt/vibmail/app/scripts/upgrade.sh \
    --archive /absolute/path/mailstack-X.Y.Z-source.zip \
    --checksum /absolute/path/mailstack-X.Y.Z-source.zip.sha256 \
    [--allow-migrations] \
    --confirm-upgrade

The deterministic source ZIP and matching SHA-256 file are both mandatory.
New Django migration files require the explicit --allow-migrations acknowledgement.
EOF
  exit 2
}

die() { printf 'UPGRADE_FINDING=%s\n' "$*" >&2; exit 1; }

[[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root"

ARCHIVE=""
CHECKSUM=""
ALLOW_MIGRATIONS=0
CONFIRM=0
while (($#)); do
  case "$1" in
    --archive) ARCHIVE=${2:?}; shift 2 ;;
    --checksum) CHECKSUM=${2:?}; shift 2 ;;
    --allow-migrations) ALLOW_MIGRATIONS=1; shift ;;
    --confirm-upgrade) CONFIRM=1; shift ;;
    -h|--help) usage ;;
    *) die "unknown option: $1" ;;
  esac
done
[[ -n "$ARCHIVE" && -n "$CHECKSUM" && $CONFIRM -eq 1 ]] || usage

ARCHIVE=$(realpath -e -- "$ARCHIVE")
CHECKSUM=$(realpath -e -- "$CHECKSUM")
[[ -f "$ARCHIVE" && ! -L "$ARCHIVE" ]] || die "target archive must be a regular non-symlink file"
[[ -f "$CHECKSUM" && ! -L "$CHECKSUM" ]] || die "checksum must be a regular non-symlink file"

APP_ROOT=${APP_ROOT:-/opt/vibmail/app}
VENV=${VENV:-/opt/vibmail/venv}
PUBLIC_ROOT=${PUBLIC_ROOT:-/opt/vibmail-public-site}
STATIC_ROOT=${STATIC_ROOT:-/var/lib/vibmail/static}
ENV_FILE=${VIBMAIL_ENV_FILE:-/etc/vibmail/vibmail.env}
MARKER_FILE=${MARKER_FILE:-/etc/vibmail/installation.json}
LOCK_FILE=${UPGRADE_LOCK_FILE:-/run/lock/vibmail-upgrade.lock}
UPGRADE_ROOT=${UPGRADE_ROOT:-/var/backups/vibmail/upgrades}
STAGING_ROOT=${STAGING_ROOT:-/opt/vibmail-upgrades}
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
VERIFY_HELPER="$SCRIPT_DIR/verify_upgrade_archive.py"

for command_name in python3 python3.12 flock rsync tar sha256sum systemctl curl nginx postfix realpath readlink; do
  command -v "$command_name" >/dev/null 2>&1 || die "required command is missing: $command_name"
done
command -v doveconf >/dev/null 2>&1 || die "required command is missing: doveconf"
[[ -f "$VERIFY_HELPER" ]] || die "upgrade archive verifier is missing: $VERIFY_HELPER"
[[ -f "$APP_ROOT/manage.py" && -f "$APP_ROOT/pyproject.toml" ]] || die "current MailStack application is incomplete"
[[ -x "$VENV/bin/python" && -x "$VENV/bin/pip" ]] || die "MailStack virtual environment is incomplete"
[[ -r "$ENV_FILE" ]] || die "environment file is missing: $ENV_FILE"
[[ -x "$APP_ROOT/scripts/backup.sh" && -x "$APP_ROOT/scripts/verify_application.sh" ]] \
  || die "current application is missing backup/verification tooling"
id -u vmail >/dev/null 2>&1 || die "required vmail user is missing"

install -d -o root -g root -m 0755 "$(dirname -- "$LOCK_FILE")"
exec 9>"$LOCK_FILE"
flock -n 9 || die "another MailStack upgrade is already running"

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a
MAIL_DOMAIN=${MAIL_DOMAIN:?MAIL_DOMAIN is missing from the environment file}
APP_HOSTNAME=${APP_HOSTNAME:?APP_HOSTNAME is missing from the environment file}
MAIL_HOSTNAME=${MAIL_HOSTNAME:?MAIL_HOSTNAME is missing from the environment file}
PUBLIC_HOSTNAME=${PUBLIC_HOSTNAME:?PUBLIC_HOSTNAME is missing from the environment file}
export VIBMAIL_ENV_FILE="$ENV_FILE"
export DJANGO_SETTINGS_MODULE=config.settings.production

run_app() {
  runuser -u vmail -- env -i \
    PATH="$VENV/bin:/usr/local/bin:/usr/bin:/bin" \
    HOME=/var/vmail USER=vmail LOGNAME=vmail \
    VIBMAIL_ENV_FILE="$ENV_FILE" \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    "$@"
}

for service in mariadb postfix dovecot nginx vibmail-gunicorn vibmail-ingestion vibmail-public-contact; do
  systemctl is-active --quiet "$service.service" || die "required service is not active before upgrade: $service"
done
postfix check
DOVECOT_CONFIG=$(doveconf -n)
[[ -n "$DOVECOT_CONFIG" ]] || die "doveconf returned no effective configuration"
nginx -t
"$APP_ROOT/scripts/verify_application.sh"

install -d -o root -g root -m 0700 "$UPGRADE_ROOT" "$STAGING_ROOT"
STAGE_PARENT=$(mktemp -d "$STAGING_ROOT/stage.XXXXXX")
cleanup_stage() { rm -rf -- "$STAGE_PARENT"; }
trap cleanup_stage EXIT

VERIFY_OUTPUT=$(
  python3 "$VERIFY_HELPER" \
    --archive "$ARCHIVE" \
    --checksum "$CHECKSUM" \
    --current-app "$APP_ROOT" \
    --extract-to "$STAGE_PARENT"
) || { printf '%s\n' "$VERIFY_OUTPUT" >&2; die "target release archive verification failed"; }
printf '%s\n' "$VERIFY_OUTPUT"
CURRENT_VERSION=$(printf '%s\n' "$VERIFY_OUTPUT" | sed -n 's/^CURRENT_VERSION=//p')
TARGET_VERSION=$(printf '%s\n' "$VERIFY_OUTPUT" | sed -n 's/^TARGET_VERSION=//p')
TARGET_ROOT=$(printf '%s\n' "$VERIFY_OUTPUT" | sed -n 's/^TARGET_ROOT=//p')
TARGET_SHA256=$(printf '%s\n' "$VERIFY_OUTPUT" | sed -n 's/^UPGRADE_ARCHIVE_SHA256=//p')
NEW_MIGRATIONS=$(printf '%s\n' "$VERIFY_OUTPUT" | sed -n 's/^NEW_MIGRATIONS=//p')
[[ "$CURRENT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-rc\.[0-9]+)?$ ]] || die "invalid current version returned by verifier"
[[ "$TARGET_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-rc\.[0-9]+)?$ ]] || die "invalid target version returned by verifier"
[[ "$TARGET_SHA256" =~ ^[0-9a-f]{64}$ ]] || die "invalid target checksum returned by verifier"
[[ "$NEW_MIGRATIONS" =~ ^[0-9]+$ ]] || die "invalid migration count returned by verifier"
[[ -d "$TARGET_ROOT/mailbox-app" && -d "$TARGET_ROOT/public-site" ]] || die "verified release staging is incomplete"
if (( NEW_MIGRATIONS > 0 && ALLOW_MIGRATIONS == 0 )); then
  die "target contains $NEW_MIGRATIONS new Django migration file(s); rerun only after review with --allow-migrations"
fi

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
ROLLBACK_ROOT="$UPGRADE_ROOT/${STAMP}-from-${CURRENT_VERSION}-to-${TARGET_VERSION}"
APP_ARCHIVE="$ROLLBACK_ROOT/application.tar.gz"
DATA_ROOT="$ROLLBACK_ROOT/data"
PUBLIC_POINTER="$ROLLBACK_ROOT/public-current.txt"
MIGRATION_RISK=0
MUTATION_STARTED=0
UPGRADE_COMPLETE=0

install -d -o root -g root -m 0700 "$ROLLBACK_ROOT" "$DATA_ROOT"
tar --one-file-system -C "$APP_ROOT" -czf "$APP_ARCHIVE" .
if [[ -f "$MARKER_FILE" ]]; then
  cp -a -- "$MARKER_FILE" "$ROLLBACK_ROOT/installation.json"
fi
CURRENT_PUBLIC=$(readlink -f -- "$PUBLIC_ROOT/current" 2>/dev/null || true)
[[ -n "$CURRENT_PUBLIC" && -d "$CURRENT_PUBLIC" ]] || die "current public-site release symlink is missing or invalid"
printf '%s\n' "$CURRENT_PUBLIC" > "$PUBLIC_POINTER"

BACKUP_OUTPUT=$(BACKUP_ROOT="$DATA_ROOT" "$APP_ROOT/scripts/backup.sh") || {
  printf '%s\n' "$BACKUP_OUTPUT" >&2
  die "pre-upgrade consistent data backup failed"
}
printf '%s\n' "$BACKUP_OUTPUT"
DATA_BACKUP=$(find "$DATA_ROOT" -mindepth 1 -maxdepth 1 -type d -print -quit)
[[ -n "$DATA_BACKUP" && -f "$DATA_BACKUP/SHA256SUMS" ]] || die "pre-upgrade data backup was not created as expected"
(cd "$DATA_BACKUP" && sha256sum --check SHA256SUMS >/dev/null)

python3 - "$ROLLBACK_ROOT/UPGRADE_METADATA.json" "$CURRENT_VERSION" "$TARGET_VERSION" \
  "$TARGET_SHA256" "$NEW_MIGRATIONS" "$DATA_BACKUP" <<'PY'
import json
import pathlib
import sys
from datetime import datetime, timezone

path = pathlib.Path(sys.argv[1])
data = {
    "format_version": 1,
    "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "current_version": sys.argv[2],
    "target_version": sys.argv[3],
    "target_archive_sha256": sys.argv[4],
    "new_migrations": int(sys.argv[5]),
    "data_backup": sys.argv[6],
}
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
path.chmod(0o600)
PY
(
  cd "$ROLLBACK_ROOT"
  files=(application.tar.gz public-current.txt UPGRADE_METADATA.json)
  [[ -f installation.json ]] && files+=(installation.json)
  sha256sum "${files[@]}" > SHA256SUMS
  sha256sum --check SHA256SUMS >/dev/null
)

restore_pre_upgrade_source() {
  local temp
  temp=$(mktemp -d "$STAGING_ROOT/rollback.XXXXXX")
  /usr/bin/python3 - "$APP_ARCHIVE" <<'PY'
import pathlib
import sys
import tarfile
archive = pathlib.Path(sys.argv[1])
with tarfile.open(archive, "r:gz") as handle:
    for member in handle.getmembers():
        path = pathlib.PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk() or member.isdev() or member.isfifo():
            raise SystemExit(f"unsafe rollback archive member: {member.name}")
PY
  tar --no-same-owner -xzf "$APP_ARCHIVE" -C "$temp"
  rsync -a --delete-delay "$temp/" "$APP_ROOT/"
  rm -rf -- "$temp"
  chown -R root:vmail "$APP_ROOT"
  find "$APP_ROOT" -type d -exec chmod 0750 {} +
  find "$APP_ROOT" -type f -exec chmod 0640 {} +
  find "$APP_ROOT/scripts" -type f -name '*.sh' -exec chmod 0750 {} +
  PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INPUT=1 \
    "$VENV/bin/pip" install --requirement "$APP_ROOT/requirements/production.txt"
  "$VENV/bin/python" -m pip check
  chown -R root:vmail "$VENV"
  chmod -R g+rX,o-rwx "$VENV"
  if [[ -f "$ROLLBACK_ROOT/installation.json" ]]; then
    cp -a -- "$ROLLBACK_ROOT/installation.json" "$MARKER_FILE"
    chown root:root "$MARKER_FILE"
    chmod 0600 "$MARKER_FILE"
  fi
  ln -sfn "$CURRENT_PUBLIC" "$PUBLIC_ROOT/current"
  run_app "$VENV/bin/python" "$APP_ROOT/manage.py" collectstatic --noinput
  chown -R vmail:www-data "$STATIC_ROOT"
  find "$STATIC_ROOT" -type d -exec chmod 0755 {} +
  find "$STATIC_ROOT" -type f -exec chmod 0644 {} +
}

rollback_on_failure() {
  local status=${1:-$?}
  trap - ERR INT TERM
  set +e
  printf 'UPGRADE_FAILURE=detected\n' >&2
  systemctl stop vibmail-public-contact.service vibmail-ingestion.service vibmail-gunicorn.service >/dev/null 2>&1 || true
  if (( MUTATION_STARTED == 1 && MIGRATION_RISK == 1 )); then
    printf 'UPGRADE_ROLLBACK=MANUAL_SCHEMA_RECONCILIATION_REQUIRED\n' >&2
    printf 'UPGRADE_ROLLBACK_SNAPSHOT=%s\n' "$ROLLBACK_ROOT" >&2
    printf 'UPGRADE_DATA_BACKUP=%s\n' "$DATA_BACKUP" >&2
    printf 'A migration-capable upgrade failed after schema mutation began; automatic source rollback is refused to avoid an unproven source/schema pairing.\n' >&2
  elif (( MUTATION_STARTED == 1 )); then
    printf 'UPGRADE_ROLLBACK=AUTO_SOURCE_RUNTIME\n' >&2
    restore_pre_upgrade_source || true
    systemctl start vibmail-gunicorn.service vibmail-ingestion.service vibmail-public-contact.service >/dev/null 2>&1 || true
    "$APP_ROOT/scripts/verify_application.sh" >/dev/null 2>&1 || true
    printf 'UPGRADE_ROLLBACK_SNAPSHOT=%s\n' "$ROLLBACK_ROOT" >&2
  fi
  exit "$status"
}
trap rollback_on_failure ERR INT TERM

# The consistent data backup above may briefly stop SMTP/LMTP. From this point onward,
# Postfix and Dovecot remain active while the web/ingestion workers are upgraded.
MUTATION_STARTED=1
systemctl stop vibmail-public-contact.service vibmail-ingestion.service vibmail-gunicorn.service
systemctl is-active --quiet postfix.service || { printf 'UPGRADE_FINDING=Postfix stopped unexpectedly before application mutation\n' >&2; rollback_on_failure 1; }
systemctl is-active --quiet dovecot.service || { printf 'UPGRADE_FINDING=Dovecot stopped unexpectedly before application mutation\n' >&2; rollback_on_failure 1; }

rsync -a --delete-delay \
  --exclude='.env' --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.pytest_cache' --exclude='.ruff_cache' --exclude='.coverage' --exclude='htmlcov' \
  --exclude='coverage.json' --exclude='coverage.xml' --exclude='staticfiles' --exclude='.runtime' \
  "$TARGET_ROOT/mailbox-app/" "$APP_ROOT/"
chown -R root:vmail "$APP_ROOT"
find "$APP_ROOT" -type d -exec chmod 0750 {} +
find "$APP_ROOT" -type f -exec chmod 0640 {} +
find "$APP_ROOT/scripts" -type f -name '*.sh' -exec chmod 0750 {} +

PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INPUT=1 \
  "$VENV/bin/pip" install --requirement "$APP_ROOT/requirements/production.txt"
"$VENV/bin/python" -m pip check
chown -R root:vmail "$VENV"
chmod -R g+rX,o-rwx "$VENV"
runuser -u vmail -- "$VENV/bin/python" -c 'import django.core, MySQLdb'

cd "$APP_ROOT"
if (( NEW_MIGRATIONS > 0 )); then
  MIGRATION_RISK=1
fi
run_app "$VENV/bin/python" manage.py migrate --noinput
run_app "$VENV/bin/python" manage.py verify_mailserver_schema
run_app "$VENV/bin/python" manage.py sync_mailserver_mailboxes --strict
run_app "$VENV/bin/python" manage.py update_mailbox_counters
run_app "$VENV/bin/python" manage.py verify_mail_storage
run_app "$VENV/bin/python" manage.py verify_postfix_contract
run_app "$VENV/bin/python" manage.py collectstatic --noinput
chown -R vmail:www-data "$STATIC_ROOT"
find "$STATIC_ROOT" -type d -exec chmod 0755 {} +
find "$STATIC_ROOT" -type f -exec chmod 0644 {} +
run_app "$VENV/bin/python" manage.py check --deploy

PUBLIC_RELEASE="$PUBLIC_ROOT/releases/${STAMP}-${TARGET_VERSION}"
[[ ! -e "$PUBLIC_RELEASE" ]] || { printf 'UPGRADE_FINDING=target public release directory already exists: %s\n' "$PUBLIC_RELEASE" >&2; rollback_on_failure 1; }
install -d -o root -g root -m 0755 "$PUBLIC_RELEASE"
rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' "$TARGET_ROOT/public-site/" "$PUBLIC_RELEASE/"
python3 "$TARGET_ROOT/scripts/render_public_site.py" \
  "$PUBLIC_RELEASE/site-template" "$PUBLIC_RELEASE/site" \
  --public-hostname "$PUBLIC_HOSTNAME" --app-hostname "$APP_HOSTNAME" \
  --mail-hostname "$MAIL_HOSTNAME" --mail-domain "$MAIL_DOMAIN"
if [[ ! -x "$PUBLIC_ROOT/venv/bin/python" ]]; then
  python3.12 -m venv "$PUBLIC_ROOT/venv"
fi
PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INPUT=1 \
  "$PUBLIC_ROOT/venv/bin/pip" install --requirement "$PUBLIC_RELEASE/requirements.txt"
"$PUBLIC_ROOT/venv/bin/python" -m pip check
chmod -R a+rX "$PUBLIC_ROOT/venv" "$PUBLIC_RELEASE"
ln -sfn "$PUBLIC_RELEASE" "$PUBLIC_ROOT/current"
ln -sfn "$PUBLIC_ROOT/current/site" "/var/www/$PUBLIC_HOSTNAME/current"

python3 - "$MARKER_FILE" "$CURRENT_VERSION" "$TARGET_VERSION" "$TARGET_SHA256" <<'PY'
import json
import pathlib
import sys
from datetime import datetime, timezone
path = pathlib.Path(sys.argv[1])
data = {}
if path.is_file():
    data = json.loads(path.read_text(encoding="utf-8"))
data.update({
    "product": data.get("product", "MailStack"),
    "previous_version": sys.argv[2],
    "version": sys.argv[3],
    "upgraded_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source_sha256": sys.argv[4],
})
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
path.chmod(0o600)
PY
chown root:root "$MARKER_FILE"
chmod 0600 "$MARKER_FILE"

postfix check
doveconf -n >/dev/null
nginx -t
systemctl daemon-reload
systemctl start vibmail-gunicorn.service vibmail-ingestion.service vibmail-public-contact.service
for service in mariadb postfix dovecot nginx vibmail-gunicorn vibmail-ingestion vibmail-public-contact; do
  systemctl is-active --quiet "$service.service" || { printf 'UPGRADE_FINDING=service is not active after upgrade: %s\n' "$service" >&2; rollback_on_failure 1; }
done
"$APP_ROOT/scripts/verify_application.sh"
curl --fail --silent --show-error --max-time 20 \
  --resolve "$APP_HOSTNAME:443:127.0.0.1" "https://$APP_HOSTNAME/accounts/login/" >/dev/null
curl --fail --silent --show-error --max-time 20 \
  --resolve "$PUBLIC_HOSTNAME:443:127.0.0.1" "https://$PUBLIC_HOSTNAME/" >/dev/null

UPGRADE_COMPLETE=1
trap - ERR INT TERM
printf 'MAILSTACK_UPGRADE=PASS\n'
printf 'UPGRADE_FROM=%s\n' "$CURRENT_VERSION"
printf 'UPGRADE_TO=%s\n' "$TARGET_VERSION"
printf 'UPGRADE_ARCHIVE_SHA256=%s\n' "$TARGET_SHA256"
printf 'UPGRADE_ROLLBACK_SNAPSHOT=%s\n' "$ROLLBACK_ROOT"
printf 'UPGRADE_DATA_BACKUP=%s\n' "$DATA_BACKUP"
printf 'INBOUND_CONTINUITY=POSTFIX_DOVECOT_LEFT_ACTIVE_DURING_SOURCE_MUTATION\n'
