#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

APP_ROOT=${APP_ROOT:-/opt/vibmail/app}
PYTHON=${PYTHON:-/opt/vibmail/venv/bin/python}
SOCKET=${SOCKET:-/run/vibmail/gunicorn.sock}
ENV_FILE=${VIBMAIL_ENV_FILE:-/etc/vibmail/vibmail.env}
[[ -r "$ENV_FILE" ]] || { printf 'Environment file is missing: %s\n' "$ENV_FILE" >&2; exit 1; }
# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a
APP_HOSTNAME=${APP_HOSTNAME:?APP_HOSTNAME is missing from the environment file}
export VIBMAIL_ENV_FILE="$ENV_FILE"
export DJANGO_SETTINGS_MODULE=config.settings.production
[[ -x "$PYTHON" && -f "$APP_ROOT/manage.py" ]] \
  || { printf 'Application runtime is incomplete.\n' >&2; exit 1; }
cd "$APP_ROOT"
"$PYTHON" manage.py check --deploy
"$PYTHON" manage.py makemigrations --check --dry-run
"$PYTHON" manage.py showmigrations --plan
"$PYTHON" manage.py verify_mailserver_schema
"$PYTHON" manage.py verify_mail_storage
"$PYTHON" manage.py verify_postfix_contract
"$PYTHON" manage.py ingest_maildir --once --dry-run
[[ -S "$SOCKET" ]] || { printf 'Gunicorn socket is missing: %s\n' "$SOCKET" >&2; exit 1; }
for endpoint in live ready; do
  curl --fail --silent --show-error --max-time 15 --unix-socket "$SOCKET" \
    -H "Host: $APP_HOSTNAME" -H 'X-Forwarded-Proto: https' \
    "http://localhost/health/$endpoint/" >/dev/null
done
printf 'Application verification completed.\n'
