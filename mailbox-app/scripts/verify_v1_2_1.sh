#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

[[ ${EUID} -eq 0 ]] || { printf 'Run as root.\n' >&2; exit 1; }
APP_ROOT=${APP_ROOT:-/opt/vibmail/app}
PYTHON=${PYTHON:-/opt/vibmail/venv/bin/python}
ENV_FILE=${VIBMAIL_ENV_FILE:-/etc/vibmail/vibmail.env}
[[ -r "$ENV_FILE" && -x "$PYTHON" && -f "$APP_ROOT/manage.py" ]] || { printf 'Application runtime is incomplete.\n' >&2; exit 1; }
grep -q '^version = "1.2.1"$' "$APP_ROOT/pyproject.toml" || { printf 'Installed source is not 1.2.1.\n' >&2; exit 1; }

for service in nginx vibmail-gunicorn vibmail-ingestion postfix dovecot mariadb; do
  systemctl is-active --quiet "$service" || { printf 'Inactive service: %s\n' "$service" >&2; exit 1; }
done
nginx -t

export VIBMAIL_ENV_FILE="$ENV_FILE"
export DJANGO_SETTINGS_MODULE=config.settings.production
run_app() {
  runuser -u vmail --preserve-environment -- env \
    VIBMAIL_ENV_FILE="$VIBMAIL_ENV_FILE" \
    DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" \
    "$@"
}
cd "$APP_ROOT"
run_app "$PYTHON" - <<'PY'
from importlib.metadata import version

required = {
    "Django": "5.2.16",
    "bleach": "6.4.0",
    "python-dotenv": "1.2.2",
}
for package, expected in required.items():
    installed = version(package)
    if installed != expected:
        raise SystemExit(f"Expected {package} {expected}, found {installed}")
    print(f"{package.upper().replace('-', '_')}_VERSION={installed}")
PY
run_app "$PYTHON" manage.py check --deploy
run_app "$PYTHON" manage.py makemigrations --check --dry-run
run_app "$PYTHON" manage.py migrate --check
run_app "$PYTHON" manage.py verify_mailserver_schema
run_app "$PYTHON" manage.py verify_mail_storage
run_app "$PYTHON" manage.py verify_postfix_contract

curl --fail --silent --show-error --max-time 15 --resolve app.vibmail.my:443:127.0.0.1 \
  https://app.vibmail.my/accounts/login/ >/dev/null
[[ $(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 15 \
  --resolve app.vibmail.my:443:127.0.0.1 https://app.vibmail.my/) == 302 ]]
[[ $(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 15 \
  --resolve app.vibmail.my:443:127.0.0.1 https://app.vibmail.my/health/ready/) == 200 ]]
[[ $(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 15 \
  --resolve app.vibmail.my:443:127.0.0.1 https://app.vibmail.my/.env) == 404 ]]
[[ $(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 15 \
  --resolve app.vibmail.my:80:127.0.0.1 http://app.vibmail.my/) == 301 ]]

STATIC_FILE=$(find /var/lib/vibmail/static -type f ! -name '*.gz' -print -quit)
[[ -n "$STATIC_FILE" ]]
STATIC_PATH=${STATIC_FILE#/var/lib/vibmail/static/}
[[ $(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 15 \
  --resolve app.vibmail.my:443:127.0.0.1 "https://app.vibmail.my/static/$STATIC_PATH") == 200 ]]

TOKEN=$(printf 'vibmail-acme-%s-%s' "$(date +%s)" "$$")
CHALLENGE_ROOT=/var/www/letsencrypt/.well-known/acme-challenge
install -d -o root -g root -m 0755 "$CHALLENGE_ROOT"
printf '%s\n' "$TOKEN" > "$CHALLENGE_ROOT/$TOKEN"
trap 'rm -f -- "$CHALLENGE_ROOT/$TOKEN"' EXIT
[[ $(curl --silent --max-time 15 --resolve app.vibmail.my:80:127.0.0.1 \
  "http://app.vibmail.my/.well-known/acme-challenge/$TOKEN") == "$TOKEN" ]]
rm -f -- "$CHALLENGE_ROOT/$TOKEN"
trap - EXIT

run_app "$PYTHON" manage.py shell -c \
  'from apps.mailboxes.models import Mailbox; from apps.messages.models import Message; print(f"APP_MAILBOXES={Mailbox.objects.count()}"); print(f"APP_MESSAGES={Message.objects.count()}")'
printf 'MAILDIR_MESSAGES=%s\n' "$(find /var/vmail/vibmail.my -type f \( -path '*/Maildir/cur/*' -o -path '*/Maildir/new/*' \) | wc -l)"
printf 'Automated production verification: PASS\n'
printf 'Manual gates still required: real inbound email, live browser update, copy action, user isolation, auto-read, delete permissions.\n'
