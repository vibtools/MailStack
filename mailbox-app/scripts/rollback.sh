#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

usage() { printf 'Usage: %s --archive /var/backups/vibmail/deployments/app-before-*.tar.gz --confirm-rollback\n' "$0" >&2; exit 2; }
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
[[ ${EUID} -eq 0 ]] || { printf 'Run as root.\n' >&2; exit 1; }
[[ ${1:-} == --archive && -n ${2:-} && ${3:-} == --confirm-rollback && $# -eq 3 ]] || usage
ARCHIVE=$(realpath -e -- "$2")
case "$ARCHIVE" in /var/backups/vibmail/deployments/*.tar.gz) ;; *) printf 'Archive path refused.\n' >&2; exit 1;; esac
validate_tar_archive "$ARCHIVE"
APP_ROOT=/opt/vibmail/app
STATIC_ROOT=/var/lib/vibmail/static
TEMP=$(mktemp -d /opt/vibmail/rollback.XXXXXX)
trap 'rm -rf -- "$TEMP"' EXIT
tar --no-same-owner -xzf "$ARCHIVE" -C "$TEMP"
[[ -f "$TEMP/manage.py" && -f "$TEMP/pyproject.toml" ]] || { printf 'Archive is not a valid application backup.\n' >&2; exit 1; }
systemctl stop vibmail-ingestion.service vibmail-gunicorn.service
rsync -a --delete-delay "$TEMP/" "$APP_ROOT/"
chown -R root:vmail "$APP_ROOT"
find "$APP_ROOT" -type d -exec chmod 0750 {} +
find "$APP_ROOT" -type f -exec chmod 0640 {} +
find "$APP_ROOT/scripts" -type f -name '*.sh' -exec chmod 0750 {} +
ENV_FILE=/etc/vibmail/vibmail.env
export VIBMAIL_ENV_FILE="$ENV_FILE"
export DJANGO_SETTINGS_MODULE=config.settings.production
run_app() {
  runuser -u vmail --preserve-environment -- env \
    VIBMAIL_ENV_FILE="$VIBMAIL_ENV_FILE" \
    DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" \
    "$@"
}

cd "$APP_ROOT"
run_app /opt/vibmail/venv/bin/python manage.py migrate --noinput
VIBMAIL_ENV_FILE="$VIBMAIL_ENV_FILE" DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" \
  STATIC_ROOT="$STATIC_ROOT" /opt/vibmail/venv/bin/python manage.py collectstatic --noinput
chown -R root:www-data "$STATIC_ROOT"
find "$STATIC_ROOT" -type d -exec chmod 0755 {} +
find "$STATIC_ROOT" -type f -exec chmod 0644 {} +
run_app /opt/vibmail/venv/bin/python manage.py check --deploy
systemctl start vibmail-gunicorn.service vibmail-ingestion.service
printf 'Application rollback completed. Database migrations are forward-safe; restore a coordinated database backup when schema rollback is required.\n'
