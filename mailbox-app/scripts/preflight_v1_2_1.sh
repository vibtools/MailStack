#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

usage() { printf 'Usage: %s --source /absolute/release/vib_mail_mvp\n' "$0" >&2; exit 2; }
[[ ${EUID} -eq 0 ]] || { printf 'Run as root.\n' >&2; exit 1; }
[[ ${1:-} == --source && -n ${2:-} && $# -eq 2 ]] || usage
SOURCE=$(realpath -e -- "$2")
case "$SOURCE" in
  /opt/vibmail/app|/opt/vibmail/app/*)
    printf 'Release source must be isolated from the live application directory.\n' >&2
    exit 1
    ;;
esac
[[ -f "$SOURCE/manage.py" && -f "$SOURCE/pyproject.toml" ]] || { printf 'Invalid release source.\n' >&2; exit 1; }
grep -q '^version = "1.2.1"$' "$SOURCE/pyproject.toml" || { printf 'Release is not version 1.2.1.\n' >&2; exit 1; }
grep -q '^Django==5\.2\.16$' "$SOURCE/requirements/locked.txt" || { printf 'Required Django 5.2.16 security pin is missing.\n' >&2; exit 1; }
grep -q '^bleach==6\.4\.0$' "$SOURCE/requirements/locked.txt" || { printf 'Required Bleach 6.4.0 security pin is missing.\n' >&2; exit 1; }
grep -q '^python-dotenv==1\.2\.2$' "$SOURCE/requirements/locked.txt" || { printf 'Required python-dotenv 1.2.2 security pin is missing.\n' >&2; exit 1; }
[[ -f "$SOURCE/RELEASE_MANIFEST.json" ]] || { printf 'Release manifest is missing.\n' >&2; exit 1; }
/usr/bin/python3 "$SOURCE/scripts/verify_release_manifest.py" "$SOURCE"
runuser -u vmail -- test -r "$SOURCE/manage.py" || {
  printf 'Release source is not readable by the vmail runtime user. Use root:vmail ownership and group traverse/read permissions.\n' >&2
  exit 1
}

ENV_FILE=/etc/vibmail/vibmail.env
PYTHON=/opt/vibmail/venv/bin/python
CURRENT_APP=/opt/vibmail/app
[[ -r "$ENV_FILE" && -x "$PYTHON" && -f "$CURRENT_APP/manage.py" ]] || { printf 'Production runtime is incomplete.\n' >&2; exit 1; }

for service in nginx vibmail-gunicorn vibmail-ingestion postfix dovecot mariadb; do
  systemctl is-active --quiet "$service" || { printf 'Inactive service: %s\n' "$service" >&2; exit 1; }
done
nginx -t

RELEASE_NGINX="$SOURCE/deployment/nginx/app.vibmail.my.conf"
[[ -r "$RELEASE_NGINX" ]] || { printf 'Release Nginx config is missing.\n' >&2; exit 1; }
! grep -q 'include[[:space:]]\+proxy_params' "$RELEASE_NGINX" || { printf 'Duplicate proxy-header risk in release config.\n' >&2; exit 1; }
[[ $(grep -c 'proxy_set_header Host \$host;' "$RELEASE_NGINX") -eq 2 ]] || { printf 'Unexpected Host-header count.\n' >&2; exit 1; }
grep -q 'location \^~ /.well-known/acme-challenge/' "$RELEASE_NGINX" || { printf 'ACME route missing.\n' >&2; exit 1; }

openssl x509 -in /etc/letsencrypt/live/app.vibmail.my/fullchain.pem -noout -checkend 604800 >/dev/null
openssl x509 -in /etc/letsencrypt/live/app.vibmail.my/fullchain.pem -noout -ext subjectAltName | grep -q 'DNS:app.vibmail.my'

export VIBMAIL_ENV_FILE="$ENV_FILE"
export DJANGO_SETTINGS_MODULE=config.settings.production
run_app() {
  runuser -u vmail --preserve-environment -- env \
    VIBMAIL_ENV_FILE="$VIBMAIL_ENV_FILE" \
    DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" \
    "$@"
}

cd "$SOURCE"
run_app "$PYTHON" manage.py check
run_app "$PYTHON" manage.py makemigrations --check --dry-run
run_app "$PYTHON" manage.py migrate --plan

cd "$CURRENT_APP"
run_app "$PYTHON" manage.py shell -c \
  'from apps.mailboxes.models import Mailbox; from apps.messages.models import Message; print(f"APP_MAILBOXES={Mailbox.objects.count()}"); print(f"APP_MESSAGES={Message.objects.count()}")'
printf 'MAILDIR_MESSAGES=%s\n' "$(find /var/vmail/vibmail.my -type f \( -path '*/Maildir/cur/*' -o -path '*/Maildir/new/*' \) | wc -l)"
printf 'MailStack 1.2.1 preflight: PASS\n'
