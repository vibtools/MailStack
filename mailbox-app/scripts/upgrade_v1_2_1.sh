#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

usage() { printf 'Usage: %s --source /absolute/release/vib_mail_mvp --confirm-upgrade\n' "$0" >&2; exit 2; }
[[ ${EUID} -eq 0 ]] || { printf 'Run as root.\n' >&2; exit 1; }
[[ ${1:-} == --source && -n ${2:-} && ${3:-} == --confirm-upgrade && $# -eq 3 ]] || usage
SOURCE=$(realpath -e -- "$2")
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
APP_ROOT=/opt/vibmail/app
STATIC_ROOT=/var/lib/vibmail/static
VENV=/opt/vibmail/venv
ENV_FILE=/etc/vibmail/vibmail.env
ROLLBACK_ROOT=/var/backups/vibmail/deployments/v1.2.1-$STAMP
APP_ARCHIVE="$ROLLBACK_ROOT/application.tar.gz"
LIVE_NGINX=/etc/nginx/sites-available/app.vibmail.my.conf
UNIT_GUNICORN=/etc/systemd/system/vibmail-gunicorn.service
UNIT_INGESTION=/etc/systemd/system/vibmail-ingestion.service
LOGROTATE=/etc/logrotate.d/vibmail
UPGRADE_COMPLETE=0

bash "$SOURCE/scripts/preflight_v1_2_1.sh" --source "$SOURCE"
bash "$SOURCE/scripts/backup.sh"

install -d -o root -g root -m 0700 "$ROLLBACK_ROOT"
tar --one-file-system -C "$APP_ROOT" -czf "$APP_ARCHIVE" .
cp -a -- "$LIVE_NGINX" "$ROLLBACK_ROOT/app.vibmail.my.conf"
cp -a -- "$UNIT_GUNICORN" "$ROLLBACK_ROOT/vibmail-gunicorn.service"
cp -a -- "$UNIT_INGESTION" "$ROLLBACK_ROOT/vibmail-ingestion.service"
cp -a -- "$LOGROTATE" "$ROLLBACK_ROOT/vibmail-logrotate"
sha256sum "$ROLLBACK_ROOT"/* > "$ROLLBACK_ROOT/SHA256SUMS"

rollback_on_failure() {
  status=$?
  trap - ERR INT TERM
  set +e
  printf 'Upgrade failure detected; restoring the pre-upgrade application and service configuration.\n' >&2
  systemctl stop vibmail-ingestion.service vibmail-gunicorn.service
  temp=$(mktemp -d /opt/vibmail/v1.2.1-rollback.XXXXXX)
  tar --no-same-owner -xzf "$APP_ARCHIVE" -C "$temp"
  rsync -a --delete-delay "$temp/" "$APP_ROOT/"
  rm -rf -- "$temp"
  chown -R root:vmail "$APP_ROOT"
  find "$APP_ROOT" -type d -exec chmod 0750 {} +
  find "$APP_ROOT" -type f -exec chmod 0640 {} +
  find "$APP_ROOT/scripts" -type f -name '*.sh' -exec chmod 0750 {} +
  cp -a -- "$ROLLBACK_ROOT/app.vibmail.my.conf" "$LIVE_NGINX"
  cp -a -- "$ROLLBACK_ROOT/vibmail-gunicorn.service" "$UNIT_GUNICORN"
  cp -a -- "$ROLLBACK_ROOT/vibmail-ingestion.service" "$UNIT_INGESTION"
  cp -a -- "$ROLLBACK_ROOT/vibmail-logrotate" "$LOGROTATE"
  systemctl daemon-reload
  if [[ -x "$VENV/bin/python" && -r "$ENV_FILE" ]]; then
    cd "$APP_ROOT" || true
    VIBMAIL_ENV_FILE="$ENV_FILE" DJANGO_SETTINGS_MODULE=config.settings.production \
      STATIC_ROOT="$STATIC_ROOT" "$VENV/bin/python" manage.py collectstatic --noinput || true
    chown -R root:www-data "$STATIC_ROOT" || true
    find "$STATIC_ROOT" -type d -exec chmod 0755 {} + || true
    find "$STATIC_ROOT" -type f -exec chmod 0644 {} + || true
  fi
  nginx -t && systemctl reload nginx || true
  systemctl start vibmail-gunicorn.service vibmail-ingestion.service || true
  printf 'Emergency source/config rollback completed. Database migrations were intentionally left forward-compatible to avoid mail loss. Backup: %s\n' "$ROLLBACK_ROOT" >&2
  exit "$status"
}
trap rollback_on_failure ERR INT TERM

systemctl stop vibmail-ingestion.service vibmail-gunicorn.service
bash "$SOURCE/scripts/deploy_application.sh" --source "$SOURCE"
install -o root -g root -m 0644 "$SOURCE/deployment/systemd/vibmail-gunicorn.service" "$UNIT_GUNICORN"
install -o root -g root -m 0644 "$SOURCE/deployment/systemd/vibmail-ingestion.service" "$UNIT_INGESTION"
install -o root -g root -m 0644 "$SOURCE/deployment/nginx/app.vibmail.my.conf" "$LIVE_NGINX"
install -o root -g root -m 0644 "$SOURCE/deployment/logrotate/vibmail" "$LOGROTATE"
nginx -t
systemctl daemon-reload
systemctl restart vibmail-gunicorn.service vibmail-ingestion.service
systemctl reload nginx
bash /opt/vibmail/app/scripts/verify_v1_2_1.sh
UPGRADE_COMPLETE=1
trap - ERR INT TERM

printf 'MailStack 1.2.1 automated upgrade completed. Rollback snapshot: %s\n' "$ROLLBACK_ROOT"
printf 'Run every manual acceptance gate before final production acceptance.\n'
