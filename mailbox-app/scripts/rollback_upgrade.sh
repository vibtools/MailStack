#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

usage() {
  cat >&2 <<'EOF'
Usage:
  sudo /opt/vibmail/app/scripts/rollback_upgrade.sh \
    --snapshot /var/backups/vibmail/upgrades/TIMESTAMP-from-X-to-Y \
    [--accept-forward-schema] \
    --confirm-rollback

This restores application/runtime source and the previous public-site pointer.
It never restores MariaDB or Maildir automatically. If the upgrade introduced migrations,
rollback fails closed unless --accept-forward-schema is explicitly supplied after review.
EOF
  exit 2
}

die() { printf 'ROLLBACK_FINDING=%s\n' "$*" >&2; exit 1; }
validate_tar_archive() {
  /usr/bin/python3 - "$1" <<'PY'
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
}

[[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root"
SNAPSHOT=""
ACCEPT_FORWARD_SCHEMA=0
CONFIRM=0
while (($#)); do
  case "$1" in
    --snapshot) SNAPSHOT=${2:?}; shift 2 ;;
    --accept-forward-schema) ACCEPT_FORWARD_SCHEMA=1; shift ;;
    --confirm-rollback) CONFIRM=1; shift ;;
    -h|--help) usage ;;
    *) die "unknown option: $1" ;;
  esac
done
[[ -n "$SNAPSHOT" && $CONFIRM -eq 1 ]] || usage
SNAPSHOT=$(realpath -e -- "$SNAPSHOT")
case "$SNAPSHOT" in
  /var/backups/vibmail/upgrades/*) ;;
  *) die "snapshot path is outside /var/backups/vibmail/upgrades" ;;
esac

APP_ROOT=${APP_ROOT:-/opt/vibmail/app}
VENV=${VENV:-/opt/vibmail/venv}
PUBLIC_ROOT=${PUBLIC_ROOT:-/opt/vibmail-public-site}
STATIC_ROOT=${STATIC_ROOT:-/var/lib/vibmail/static}
ENV_FILE=${VIBMAIL_ENV_FILE:-/etc/vibmail/vibmail.env}
MARKER_FILE=${MARKER_FILE:-/etc/vibmail/installation.json}
LOCK_FILE=${UPGRADE_LOCK_FILE:-/run/lock/vibmail-upgrade.lock}
STAGING_ROOT=${STAGING_ROOT:-/opt/vibmail-upgrades}
for command_name in python3 flock rsync tar sha256sum systemctl realpath postfix doveconf nginx; do
  command -v "$command_name" >/dev/null 2>&1 || die "required command is missing: $command_name"
done
for required in application.tar.gz public-current.txt UPGRADE_METADATA.json SHA256SUMS; do
  [[ -f "$SNAPSHOT/$required" ]] || die "snapshot is incomplete: $required is missing"
done
(cd "$SNAPSHOT" && sha256sum --check SHA256SUMS)
validate_tar_archive "$SNAPSHOT/application.tar.gz"

NEW_MIGRATIONS=$(python3 - "$SNAPSHOT/UPGRADE_METADATA.json" <<'PY'
import json, pathlib, sys
payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
print(int(payload.get("new_migrations", 0)))
PY
)
DATA_BACKUP=$(python3 - "$SNAPSHOT/UPGRADE_METADATA.json" <<'PY'
import json, pathlib, sys
payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload.get("data_backup", ""))
PY
)
[[ "$NEW_MIGRATIONS" =~ ^[0-9]+$ ]] || die "snapshot migration metadata is invalid"
if (( NEW_MIGRATIONS > 0 && ACCEPT_FORWARD_SCHEMA == 0 )); then
  die "snapshot belongs to an upgrade with new migrations; review coordinated data restore/reconciliation or explicitly accept the forward schema"
fi

install -d -o root -g root -m 0755 "$(dirname -- "$LOCK_FILE")" "$STAGING_ROOT"
exec 9>"$LOCK_FILE"
flock -n 9 || die "another MailStack upgrade/rollback is already running"
[[ -r "$ENV_FILE" ]] || die "environment file is missing: $ENV_FILE"
# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a
export VIBMAIL_ENV_FILE="$ENV_FILE"
export DJANGO_SETTINGS_MODULE=config.settings.production
run_app() {
  runuser -u vmail -- env -i \
    PATH="$VENV/bin:/usr/local/bin:/usr/bin:/bin" \
    HOME=/var/vmail USER=vmail LOGNAME=vmail \
    VIBMAIL_ENV_FILE="$ENV_FILE" DJANGO_SETTINGS_MODULE=config.settings.production \
    "$@"
}

PREVIOUS_PUBLIC=$(cat "$SNAPSHOT/public-current.txt")
[[ "$PREVIOUS_PUBLIC" == "$PUBLIC_ROOT/releases/"* && -d "$PREVIOUS_PUBLIC" ]] \
  || die "snapshot public-site pointer is invalid"
TEMP=$(mktemp -d "$STAGING_ROOT/rollback.XXXXXX")
trap 'rm -rf -- "$TEMP"' EXIT
systemctl stop vibmail-public-contact.service vibmail-ingestion.service vibmail-gunicorn.service

tar --no-same-owner -xzf "$SNAPSHOT/application.tar.gz" -C "$TEMP"
[[ -f "$TEMP/manage.py" && -f "$TEMP/pyproject.toml" ]] || die "snapshot application archive is invalid"
rsync -a --delete-delay "$TEMP/" "$APP_ROOT/"
chown -R root:vmail "$APP_ROOT"
find "$APP_ROOT" -type d -exec chmod 0750 {} +
find "$APP_ROOT" -type f -exec chmod 0640 {} +
find "$APP_ROOT/scripts" -type f -name '*.sh' -exec chmod 0750 {} +
PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INPUT=1 \
  "$VENV/bin/pip" install --requirement "$APP_ROOT/requirements/production.txt"
"$VENV/bin/python" -m pip check
chown -R root:vmail "$VENV"
chmod -R g+rX,o-rwx "$VENV"

if [[ -f "$SNAPSHOT/installation.json" ]]; then
  cp -a -- "$SNAPSHOT/installation.json" "$MARKER_FILE"
  chown root:root "$MARKER_FILE"
  chmod 0600 "$MARKER_FILE"
fi
ln -sfn "$PREVIOUS_PUBLIC" "$PUBLIC_ROOT/current"
if [[ -n ${PUBLIC_HOSTNAME:-} ]]; then
  ln -sfn "$PUBLIC_ROOT/current/site" "/var/www/$PUBLIC_HOSTNAME/current"
fi

cd "$APP_ROOT"
run_app "$VENV/bin/python" manage.py collectstatic --noinput
chown -R vmail:www-data "$STATIC_ROOT"
find "$STATIC_ROOT" -type d -exec chmod 0755 {} +
find "$STATIC_ROOT" -type f -exec chmod 0644 {} +
run_app "$VENV/bin/python" manage.py check --deploy
postfix check
doveconf -n >/dev/null
nginx -t
systemctl daemon-reload
systemctl start vibmail-gunicorn.service vibmail-ingestion.service vibmail-public-contact.service
"$APP_ROOT/scripts/verify_application.sh"

printf 'MAILSTACK_ROLLBACK=PASS\n'
printf 'ROLLBACK_SNAPSHOT=%s\n' "$SNAPSHOT"
printf 'ROLLBACK_DATABASE_ACTION=NOT_PERFORMED\n'
printf 'ROLLBACK_DATA_BACKUP=%s\n' "$DATA_BACKUP"
if (( NEW_MIGRATIONS > 0 )); then
  printf 'ROLLBACK_SCHEMA=FORWARD_SCHEMA_EXPLICITLY_ACCEPTED\n'
else
  printf 'ROLLBACK_SCHEMA=UNCHANGED\n'
fi
