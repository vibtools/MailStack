#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

ENV_FILE=${VIBMAIL_ENV_FILE:-/etc/vibmail/vibmail.env}
if [[ -r "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "$ENV_FILE"
  set +a
fi
APP_HOSTNAME=${APP_HOSTNAME:-app.vibmail.my}
PUBLIC_URL=${PUBLIC_URL:-https://$APP_HOSTNAME}
SOCKET=${SOCKET:-/run/vibmail/gunicorn.sock}
curl --fail --silent --show-error --max-time 10 "$PUBLIC_URL/health/live/"
printf '\n'
[[ -S "$SOCKET" ]] || { printf 'Gunicorn socket is missing: %s\n' "$SOCKET" >&2; exit 1; }
curl --fail --silent --show-error --max-time 15 --unix-socket "$SOCKET" \
  -H "Host: $APP_HOSTNAME" -H 'X-Forwarded-Proto: https' \
  http://localhost/health/ready/
printf '\n'
