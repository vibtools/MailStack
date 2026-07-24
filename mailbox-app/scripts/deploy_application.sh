#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

usage() { printf 'Usage: %s --source /absolute/release/path\n' "$0" >&2; exit 2; }
[[ ${EUID} -eq 0 ]] || { printf 'Run as root.\n' >&2; exit 1; }
[[ ${1:-} == --source && -n ${2:-} && $# -eq 2 ]] || usage
SOURCE=$(realpath -e -- "$2")
APP_ROOT=/opt/vibmail/app
BACKUP_ROOT=/var/backups/vibmail/deployments
VENV=/opt/vibmail/venv
STATIC_ROOT=/var/lib/vibmail/static
STAMP=$(date -u +%Y%m%dT%H%M%SZ)

[[ -f "$SOURCE/manage.py" && -f "$SOURCE/pyproject.toml" ]] || { printf 'Source is not a MailStack release.\n' >&2; exit 1; }
case "$SOURCE" in
  /|/opt|/opt/vibmail|/var|/etc|"$APP_ROOT"|"$APP_ROOT"/*)
    printf 'Unsafe source path refused.\n' >&2
    exit 1
    ;;
esac
[[ -x "$VENV/bin/python" ]] || { printf 'Virtual environment is missing.\n' >&2; exit 1; }
id -u vmail >/dev/null 2>&1 || { printf 'Required vmail service user is missing.\n' >&2; exit 1; }
[[ $(id -u vmail) == 5000 && $(id -g vmail) == 5000 ]] || { printf 'vmail must use UID/GID 5000.\n' >&2; exit 1; }
ENV_FILE=/etc/vibmail/vibmail.env
[[ -r "$ENV_FILE" ]] || { printf 'Create %s before deployment.\n' "$ENV_FILE" >&2; exit 1; }
export VIBMAIL_ENV_FILE="$ENV_FILE"
export DJANGO_SETTINGS_MODULE=config.settings.production

run_app() {
  runuser -u vmail --preserve-environment -- env \
    VIBMAIL_ENV_FILE="$VIBMAIL_ENV_FILE" \
    DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" \
    "$@"
}

install -d -o root -g vmail -m 0750 "$APP_ROOT" /etc/vibmail
install -d -o root -g root -m 0700 "$BACKUP_ROOT"
install -d -o vmail -g vmail -m 0750 /var/vmail /var/vmail/vibmail.my
install -d -o vmail -g vmail -m 0700 /var/lib/vibmail/attachments
install -d -o vmail -g adm -m 0750 /var/log/vibmail
install -d -o root -g www-data -m 0755 "$STATIC_ROOT"
install -o vmail -g adm -m 0640 /dev/null /var/log/vibmail/application.log

if [[ -n $(find "$APP_ROOT" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  tar --one-file-system -C "$APP_ROOT" -czf "$BACKUP_ROOT/app-before-$STAMP.tar.gz" .
fi
rsync -a --delete-delay \
  --exclude='.env' --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.pytest_cache' --exclude='.ruff_cache' --exclude='.coverage' --exclude='htmlcov' \
  --exclude='coverage.json' --exclude='coverage.xml' --exclude='staticfiles' --exclude='.runtime' \
  "$SOURCE/" "$APP_ROOT/"
chown -R root:vmail "$APP_ROOT"
find "$APP_ROOT" -type d -exec chmod 0750 {} +
find "$APP_ROOT" -type f -exec chmod 0640 {} +
find "$APP_ROOT/scripts" -type f -name '*.sh' -exec chmod 0750 {} +

"$VENV/bin/pip" install --requirement "$APP_ROOT/requirements/production.txt" --constraint "$APP_ROOT/requirements/constraints.txt"
# pip honours the invoking root umask and can create root:root 0750 package
# directories. Normalize the complete virtualenv for the vmail runtime before
# any least-privilege management command executes.
chown -R root:vmail "$VENV"
chmod -R g+rX,o-rwx "$VENV"
runuser -u vmail -- test -x "$VENV/lib/python3.12/site-packages"
runuser -u vmail -- "$VENV/bin/python" -c 'import django.core, MySQLdb'
runuser -u vmail -- "$VENV/bin/python" - <<'PY'
from importlib.metadata import version

required = {
    "Django": "5.2.15",
    "bleach": "6.4.0",
    "python-dotenv": "1.2.2",
}
for package, expected in required.items():
    installed = version(package)
    if installed != expected:
        raise SystemExit(f"Expected {package} {expected}, found {installed}")
    print(f"{package.upper().replace('-', '_')}_VERSION={installed}")
PY
cd "$APP_ROOT"
run_app "$VENV/bin/python" manage.py migrate --noinput
run_app "$VENV/bin/python" manage.py verify_mailserver_schema
run_app "$VENV/bin/python" manage.py sync_mailserver_mailboxes --strict
run_app "$VENV/bin/python" manage.py verify_mail_storage
run_app "$VENV/bin/python" manage.py verify_postfix_contract
VIBMAIL_ENV_FILE="$VIBMAIL_ENV_FILE" DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" STATIC_ROOT="$STATIC_ROOT" "$VENV/bin/python" manage.py collectstatic --noinput
chown -R root:www-data "$STATIC_ROOT"
find "$STATIC_ROOT" -type d -exec chmod 0755 {} +
find "$STATIC_ROOT" -type f -exec chmod 0644 {} +
run_app "$VENV/bin/python" manage.py check --deploy
systemctl daemon-reload
printf 'Application files deployed. Enable or restart services only after Phase 2 configuration review.\n'
