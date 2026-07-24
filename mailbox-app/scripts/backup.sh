#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

[[ ${EUID:-$(id -u)} -eq 0 ]] || { printf 'Run as root.\n' >&2; exit 1; }

ENV_FILE=${VIBMAIL_ENV_FILE:-/etc/vibmail/vibmail.env}
[[ -r "$ENV_FILE" ]] || { printf 'Environment file is missing: %s\n' "$ENV_FILE" >&2; exit 1; }
# The installer creates this root-owned, shell-compatible environment file.
# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

BACKUP_ROOT=${BACKUP_ROOT:-/var/backups/vibmail}
DB_DEFAULTS_FILE=${DB_BACKUP_DEFAULTS_FILE:-/etc/vibmail/mariadb-backup.cnf}
DB_NAME=${DB_NAME:-vibmail_app}
MAILSERVER_DB_NAME=${MAILSERVER_DB_NAME:-vibmail}
MAIL_DOMAIN=${MAIL_DOMAIN:?MAIL_DOMAIN is missing from the environment file}
APP_HOSTNAME=${APP_HOSTNAME:?APP_HOSTNAME is missing from the environment file}
MAIL_HOSTNAME=${MAIL_HOSTNAME:?MAIL_HOSTNAME is missing from the environment file}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
DEST="$BACKUP_ROOT/$STAMP"

[[ "$BACKUP_ROOT" == /* ]] || { printf 'BACKUP_ROOT must be absolute.\n' >&2; exit 1; }
case "$BACKUP_ROOT" in
  /|/var|/var/backups|/etc|/opt) printf 'Unsafe BACKUP_ROOT refused.\n' >&2; exit 1 ;;
esac
[[ "$DB_NAME" =~ ^[A-Za-z0-9_]+$ && "$MAILSERVER_DB_NAME" =~ ^[A-Za-z0-9_]+$ ]] \
  || { printf 'Unsafe database identifier.\n' >&2; exit 1; }
[[ -d /var/vmail ]] || { printf 'Maildir root is missing.\n' >&2; exit 1; }
[[ -d /var/lib/vibmail/attachments ]] || { printf 'Attachment root is missing.\n' >&2; exit 1; }
for command_name in mariadb-dump gzip tar sha256sum systemctl python3; do
  command -v "$command_name" >/dev/null 2>&1 \
    || { printf 'Required command is missing: %s\n' "$command_name" >&2; exit 1; }
done

CONFIG_PATHS=(
  etc/vibmail/vibmail.env
  etc/systemd/system/vibmail-gunicorn.service
  etc/systemd/system/vibmail-ingestion.service
  etc/postfix/main.cf
  etc/postfix/master.cf
  etc/postfix/mysql-virtual-domains.cf
  etc/postfix/mysql-virtual-mailboxes.cf
  etc/postfix/mysql-virtual-aliases.cf
)
for relative in "${CONFIG_PATHS[@]}"; do
  [[ -f "/$relative" ]] \
    || { printf 'Required configuration is missing: /%s\n' "$relative" >&2; exit 1; }
done

# New public installer layout, with v1.2.x alternatives retained.
if [[ -f /etc/nginx/sites-available/vibmail-app.conf && -f /etc/nginx/sites-available/vibmail-public.conf ]]; then
  CONFIG_PATHS+=(
    etc/nginx/sites-available/vibmail-app.conf
    etc/nginx/sites-available/vibmail-public.conf
  )
elif [[ -f /etc/nginx/sites-available/app.vibmail.my.conf ]]; then
  CONFIG_PATHS+=(etc/nginx/sites-available/app.vibmail.my.conf)
else
  printf 'No supported MailStack Nginx configuration was found.\n' >&2
  exit 1
fi

if [[ -f /etc/dovecot/conf.d/99-vibmail.conf ]]; then
  CONFIG_PATHS+=(etc/dovecot/conf.d/99-vibmail.conf)
elif [[ -f /etc/dovecot/dovecot.conf ]]; then
  CONFIG_PATHS+=(etc/dovecot/dovecot.conf)
  [[ -f /etc/dovecot/dovecot-sql.conf.ext ]] \
    && CONFIG_PATHS+=(etc/dovecot/dovecot-sql.conf.ext)
else
  printf 'No supported Dovecot configuration was found.\n' >&2
  exit 1
fi

OPTIONAL_CONFIG_PATHS=(
  etc/vibmail/installer-secrets.env
  etc/vibmail/installation.json
  etc/vibmail/mariadb-backup.cnf
  etc/vibmail-public-contact/contact.env
  etc/systemd/system/vibmail-public-contact.service
  etc/logrotate.d/vibmail
)
for relative in "${OPTIONAL_CONFIG_PATHS[@]}"; do
  [[ -f "/$relative" ]] && CONFIG_PATHS+=("$relative")
done


install -d -m 0700 "$DEST"

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

DUMP_OPTIONS=(--protocol=socket)
if [[ -r "$DB_DEFAULTS_FILE" ]]; then
  DUMP_OPTIONS=(--defaults-extra-file="$DB_DEFAULTS_FILE")
fi
mariadb-dump "${DUMP_OPTIONS[@]}" \
  --single-transaction --add-drop-database --routines --events --triggers --hex-blob \
  --databases "$DB_NAME" "$MAILSERVER_DB_NAME" \
  | gzip -9 > "$DEST/databases.sql.gz"

tar --acls --xattrs --numeric-owner --one-file-system \
  -C /var -czf "$DEST/maildir.tar.gz" vmail
tar --acls --xattrs --numeric-owner --one-file-system \
  -C /var/lib -czf "$DEST/attachments.tar.gz" vibmail/attachments
if [[ -d /var/lib/vibmail-public-contact ]]; then
  tar --acls --xattrs --numeric-owner --one-file-system \
    -C /var/lib -czf "$DEST/contact-state.tar.gz" vibmail-public-contact
else
  tar -C /var/lib -czf "$DEST/contact-state.tar.gz" --files-from /dev/null
fi
tar --acls --xattrs --numeric-owner -C / \
  -czf "$DEST/configuration.tar.gz" "${CONFIG_PATHS[@]}"

python3 - "$DEST/BACKUP_METADATA.json" "$STAMP" "$MAIL_DOMAIN" "$APP_HOSTNAME" \
  "$MAIL_HOSTNAME" "$DB_NAME" "$MAILSERVER_DB_NAME" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = {
    "format_version": 2,
    "created_at_utc": sys.argv[2],
    "mail_domain": sys.argv[3],
    "app_hostname": sys.argv[4],
    "mail_hostname": sys.argv[5],
    "application_database": sys.argv[6],
    "mail_database": sys.argv[7],
}
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
path.chmod(0o600)
PY

for archive in databases.sql.gz maildir.tar.gz attachments.tar.gz contact-state.tar.gz configuration.tar.gz; do
  case "$archive" in
    databases.sql.gz) gzip -t "$DEST/$archive" ;;
    *) tar -tzf "$DEST/$archive" >/dev/null ;;
  esac
done
sha256sum \
  "$DEST/databases.sql.gz" \
  "$DEST/maildir.tar.gz" \
  "$DEST/attachments.tar.gz" \
  "$DEST/contact-state.tar.gz" \
  "$DEST/configuration.tar.gz" \
  "$DEST/BACKUP_METADATA.json" \
  > "$DEST/SHA256SUMS"
(cd "$DEST" && sha256sum --check SHA256SUMS >/dev/null)

trap - EXIT INT TERM
restart_services
printf 'Backup created and verified at %s\n' "$DEST"
