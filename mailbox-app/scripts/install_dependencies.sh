#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

[[ ${EUID} -eq 0 ]] || { printf 'Run as root.\n' >&2; exit 1; }
[[ -r /etc/os-release ]] || { printf 'Unsupported operating system.\n' >&2; exit 1; }
# shellcheck source=/dev/null
source /etc/os-release
if [[ ${ID:-} != ubuntu || ${VERSION_ID:-} != 24.04* ]]; then
  printf 'Ubuntu Server 24.04 LTS is required; found %s %s.\n' "${ID:-unknown}" "${VERSION_ID:-unknown}" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  python3.12 python3.12-venv python3-pip python3.12-dev build-essential pkg-config \
  default-libmysqlclient-dev mariadb-client nginx rsync curl ca-certificates

if ! getent group vmail >/dev/null; then
  groupadd --system --gid 5000 vmail
elif [[ $(getent group vmail | cut -d: -f3) != 5000 ]]; then
  printf 'Existing vmail group must use GID 5000.\n' >&2
  exit 1
fi
if ! id -u vmail >/dev/null 2>&1; then
  useradd --system --uid 5000 --gid vmail --home-dir /var/vmail --no-create-home --shell /usr/sbin/nologin vmail
elif [[ $(id -u vmail) != 5000 || $(id -g vmail) != 5000 ]]; then
  printf 'Existing vmail user must use UID/GID 5000.\n' >&2
  exit 1
fi

install -d -o vmail -g vmail -m 0750 /var/vmail /var/vmail/vibmail.my
if [[ ! -x /opt/vibmail/venv/bin/python ]]; then
  install -d -o root -g vmail -m 0750 /opt/vibmail
  python3.12 -m venv /opt/vibmail/venv
fi
/opt/vibmail/venv/bin/python -m pip install --upgrade pip setuptools wheel
chown -R root:vmail /opt/vibmail/venv
chmod -R g+rX,o-rwx /opt/vibmail/venv
runuser -u vmail -- test -x /opt/vibmail/venv/lib/python3.12/site-packages
printf 'MariaDB-compatible dependencies, service identity, and virtual environment prepared.\n'
