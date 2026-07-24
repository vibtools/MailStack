#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

[[ ${EUID} -eq 0 ]] || { printf 'Run as root.\n' >&2; exit 1; }
ENV_FILE=/etc/vibmail/vibmail.env
[[ -r "$ENV_FILE" ]] || { printf 'Environment file is missing.\n' >&2; exit 1; }
export VIBMAIL_ENV_FILE="$ENV_FILE"
export DJANGO_SETTINGS_MODULE=config.settings.production
cd /opt/vibmail/app
exec runuser -u vmail --preserve-environment -- env \
  VIBMAIL_ENV_FILE="$VIBMAIL_ENV_FILE" \
  DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" \
  /opt/vibmail/venv/bin/python manage.py create_initial_admin "$@"
