#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

usage() {
  printf 'Usage: %s --backup /absolute/path --confirm-restore\n' "$0" >&2
  exit 2
}

validate_tar_archive() {
  /usr/bin/python3 - "$1" <<'PY'
import pathlib
import sys
import tarfile

archive = pathlib.Path(sys.argv[1])
with tarfile.open(archive, "r:gz") as handle:
    for member in handle.getmembers():
        path = pathlib.PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"Unsafe archive member: {member.name}")
        if member.issym() or member.islnk() or member.isdev() or member.isfifo():
            raise SystemExit(f"Unsupported archive member type: {member.name}")
PY
}

[[ ${EUID:-$(id -u)} -eq 0 ]] || { printf 'Run as root.\n' >&2; exit 1; }
[[ ${1:-} == --backup && -n ${2:-} && ${3:-} == --confirm-restore && $# -eq 3 ]] || usage
BACKUP=$(realpath -e -- "$2")
case "$BACKUP" in /|/etc|/opt|/var|/var/backups) printf 'Unsafe backup path refused.\n' >&2; exit 1;; esac

REQUIRED=(databases.sql.gz maildir.tar.gz attachments.tar.gz configuration.tar.gz SHA256SUMS)
for required in "${REQUIRED[@]}"; do
  [[ -f "$BACKUP/$required" ]] \
    || { printf 'Incomplete backup: %s is missing.\n' "$required" >&2; exit 1; }
done
(cd "$BACKUP" && sha256sum --check SHA256SUMS)
gzip -t "$BACKUP/databases.sql.gz"
validate_tar_archive "$BACKUP/maildir.tar.gz"
validate_tar_archive "$BACKUP/attachments.tar.gz"
validate_tar_archive "$BACKUP/configuration.tar.gz"
if [[ -f "$BACKUP/contact-state.tar.gz" ]]; then
  validate_tar_archive "$BACKUP/contact-state.tar.gz"
fi

SERVICES=(vibmail-public-contact postfix dovecot vibmail-ingestion vibmail-gunicorn)
ACTIVE_SERVICES=()
for service in "${SERVICES[@]}"; do
  if systemctl is-active --quiet "$service.service"; then
    ACTIVE_SERVICES+=("$service")
  fi
done
restart_services() {
  local index
  for ((index=${#ACTIVE_SERVICES[@]}-1; index>=0; index--)); do
    systemctl start "${ACTIVE_SERVICES[$index]}.service" || true
  done
}
cleanup_on_exit() {
  local status=$?
  restart_services
  exit "$status"
}
trap cleanup_on_exit EXIT INT TERM

for service in "${SERVICES[@]}"; do
  systemctl stop "$service.service" 2>/dev/null || true
done

DB_DEFAULTS_FILE=${DB_BACKUP_DEFAULTS_FILE:-/etc/vibmail/mariadb-backup.cnf}
DB_OPTIONS=(--protocol=socket)
if [[ -r "$DB_DEFAULTS_FILE" ]]; then
  DB_OPTIONS=(--defaults-extra-file="$DB_DEFAULTS_FILE")
fi
gzip -dc "$BACKUP/databases.sql.gz" | mariadb "${DB_OPTIONS[@]}" --binary-mode

tar --numeric-owner -C /var -xzf "$BACKUP/maildir.tar.gz"
tar --numeric-owner -C /var/lib -xzf "$BACKUP/attachments.tar.gz"
if [[ -f "$BACKUP/contact-state.tar.gz" ]]; then
  tar --numeric-owner -C /var/lib -xzf "$BACKUP/contact-state.tar.gz"
fi
tar --numeric-owner -C / -xzf "$BACKUP/configuration.tar.gz"

chown -R vmail:vmail /var/vmail /var/lib/vibmail/attachments
if [[ -d /var/lib/vibmail-public-contact ]]; then
  chown -R vibmail-contact:www-data /var/lib/vibmail-public-contact
  chmod 0700 /var/lib/vibmail-public-contact
fi
chown root:vmail /etc/vibmail/vibmail.env
chmod 0640 /etc/vibmail/vibmail.env
if [[ -f /etc/vibmail/installer-secrets.env ]]; then
  chown root:root /etc/vibmail/installer-secrets.env
  chmod 0600 /etc/vibmail/installer-secrets.env
fi
if [[ -f /etc/vibmail-public-contact/contact.env ]]; then
  chown root:root /etc/vibmail-public-contact/contact.env
  chmod 0600 /etc/vibmail-public-contact/contact.env
fi
if [[ -f "$DB_DEFAULTS_FILE" ]]; then
  chown root:root "$DB_DEFAULTS_FILE"
  chmod 0600 "$DB_DEFAULTS_FILE"
fi

ENV_FILE=/etc/vibmail/vibmail.env
export VIBMAIL_ENV_FILE="$ENV_FILE"
export DJANGO_SETTINGS_MODULE=config.settings.production
run_app() {
  runuser -u vmail --preserve-environment -- env \
    VIBMAIL_ENV_FILE="$VIBMAIL_ENV_FILE" \
    DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" \
    "$@"
}

cd /opt/vibmail/app
run_app /opt/vibmail/venv/bin/python manage.py migrate --noinput
run_app /opt/vibmail/venv/bin/python manage.py verify_mailserver_schema
run_app /opt/vibmail/venv/bin/python manage.py sync_mailserver_mailboxes --strict
run_app /opt/vibmail/venv/bin/python manage.py update_mailbox_counters
run_app /opt/vibmail/venv/bin/python manage.py verify_mail_storage
run_app /opt/vibmail/venv/bin/python manage.py verify_postfix_contract
run_app /opt/vibmail/venv/bin/python manage.py collectstatic --noinput
chown -R vmail:www-data /var/lib/vibmail/static
find /var/lib/vibmail/static -type d -exec chmod 0755 {} +
find /var/lib/vibmail/static -type f -exec chmod 0644 {} +

systemctl daemon-reload
postfix check
if command -v doveconf >/dev/null 2>&1; then doveconf -n >/dev/null; fi
nginx -t

trap - EXIT INT TERM
restart_services
printf 'Restore completed and configuration validated; run scripts/verify_application.sh.\n'
