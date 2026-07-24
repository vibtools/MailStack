#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

PROJECT_NAME="MailStack"
SOURCE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_VERSION="$(tr -d '\r\n' < "$SOURCE_ROOT/VERSION")"
LOG_FILE="/var/log/vibmail-installer.log"
LOCK_FILE="/run/lock/vibmail-installer.lock"
MARKER_FILE="/etc/vibmail/installation.json"
SECRETS_FILE="/etc/vibmail/installer-secrets.env"
CERT_NAME="vibmail-stack"
MAIL_DB_NAME="vibmail"
APP_DB_NAME="vibmail_app"
APP_DB_USER="vibmail_app"
POSTFIX_DB_USER="vibmail_postfix"
ENABLE_WWW=0
PLAN_ONLY=0
NON_INTERACTIVE=0
REPAIR=0
SKIP_DNS_CHECK=0
CURRENT_PHASE="argument-validation"

MAIL_DOMAIN="${VIBMAIL_MAIL_DOMAIN:-}"
APP_HOSTNAME="${VIBMAIL_APP_HOSTNAME:-}"
MAIL_HOSTNAME="${VIBMAIL_MAIL_HOSTNAME:-}"
PUBLIC_HOSTNAME="${VIBMAIL_PUBLIC_HOSTNAME:-}"
ADMIN_EMAIL="${VIBMAIL_ADMIN_EMAIL:-}"
ADMIN_USERNAME="${VIBMAIL_ADMIN_USERNAME:-admin}"
TLS_EMAIL="${VIBMAIL_TLS_EMAIL:-}"
SERVER_IP="${VIBMAIL_SERVER_IP:-}"
ADMIN_PASSWORD_ENV="${VIBMAIL_ADMIN_PASSWORD_ENV:-}"

usage() {
  cat <<'EOF'
MailStack one-command installer for a clean Ubuntu Server 24.04 LTS VPS.

Usage:
  sudo ./install.sh [options]

Options:
  --domain DOMAIN          Mail domain, for example example.com
  --app-host HOST          Web application hostname (default: app.DOMAIN)
  --mail-host HOST         SMTP hostname (default: mail.DOMAIN)
  --public-host HOST       Public website hostname (default: DOMAIN)
  --admin-email EMAIL      Contact recipient and default TLS email
  --admin-user USER        Initial Django administrator username (default: admin)
  --admin-password-env VAR Read initial administrator password from environment VAR
  --tls-email EMAIL        Let's Encrypt account email (default: admin email)
  --server-ip IP           Public server IP (auto-detected when omitted)
  --www                    Include www.PUBLIC_HOST in the TLS certificate
  --non-interactive        Fail instead of prompting for missing values
  --repair                 Re-render and verify an existing installation using saved secrets
  --skip-dns-check         Skip DNS/MX preflight (not recommended for production)
  --plan                   Validate inputs and print the installation plan without changes
  -h, --help               Show this help

Environment equivalents use the VIBMAIL_ prefix, such as VIBMAIL_MAIL_DOMAIN.
EOF
}

log() {
  if [[ -w "$(dirname -- "$LOG_FILE")" ]]; then
    printf '%s %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*" | tee -a "$LOG_FILE" >&2
  else
    printf '%s %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*" >&2
  fi
}

die() {
  log "ERROR: $*"
  exit 1
}

on_error() {
  local status=$?
  local line=${BASH_LINENO[0]:-unknown}
  trap - ERR
  log "INSTALL_FAILURE phase=$CURRENT_PHASE line=$line exit=$status"
  if [[ -n ${BACKUP_ROOT:-} ]]; then
    log "Installer backup directory: $BACKUP_ROOT"
  fi
  if [[ -r $SECRETS_FILE ]]; then
    log "Generated secrets were retained in $SECRETS_FILE for reviewed --repair recovery"
  fi
  exit "$status"
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command is missing: $1"
}

valid_hostname() {
  local hostname=${1%.}
  local label
  local -a labels=()
  [[ ${#hostname} -le 253 && "$hostname" == *.* && "$hostname" != *..* ]] || return 1
  IFS='.' read -r -a labels <<< "$hostname"
  for label in "${labels[@]}"; do
    [[ ${#label} -ge 1 && ${#label} -le 63 ]] || return 1
    [[ "$label" =~ ^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$ ]] || return 1
  done
}

valid_email() {
  [[ "$1" =~ ^[A-Za-z0-9.!#$%\&\'*+/=?^_\`\{|\}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]
}

prompt_value() {
  local variable_name=$1 prompt_text=$2 current_value=${!1:-}
  if [[ -n "$current_value" ]]; then
    return
  fi
  (( NON_INTERACTIVE == 0 )) || die "$variable_name is required in non-interactive mode"
  read -r -p "$prompt_text: " current_value
  printf -v "$variable_name" '%s' "$current_value"
}

random_hex() {
  openssl rand -hex "$1"
}

render() {
  local template=$1 output=$2 mode=${3:-0644}
  python3 "$SOURCE_ROOT/scripts/render_template.py" \
    "$SOURCE_ROOT/deployment/templates/$template" "$output" --mode "$mode"
}

backup_file() {
  local path=$1
  [[ -e "$path" || -L "$path" ]] || return 0
  local relative=${path#/}
  install -d -m 0700 "$BACKUP_ROOT/$(dirname -- "$relative")"
  cp -a -- "$path" "$BACKUP_ROOT/$relative"
}

run_as_vmail() {
  runuser -u vmail --preserve-environment -- env \
    VIBMAIL_ENV_FILE=/etc/vibmail/vibmail.env \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    "$@"
}

for argument in "$@"; do
  case "$argument" in
    -h|--help) usage; exit 0 ;;
  esac
done

while (($#)); do
  case "$1" in
    --domain) MAIL_DOMAIN=${2:?}; shift 2 ;;
    --app-host) APP_HOSTNAME=${2:?}; shift 2 ;;
    --mail-host) MAIL_HOSTNAME=${2:?}; shift 2 ;;
    --public-host) PUBLIC_HOSTNAME=${2:?}; shift 2 ;;
    --admin-email) ADMIN_EMAIL=${2:?}; shift 2 ;;
    --admin-user) ADMIN_USERNAME=${2:?}; shift 2 ;;
    --admin-password-env) ADMIN_PASSWORD_ENV=${2:?}; shift 2 ;;
    --tls-email) TLS_EMAIL=${2:?}; shift 2 ;;
    --server-ip) SERVER_IP=${2:?}; shift 2 ;;
    --www) ENABLE_WWW=1; shift ;;
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    --repair) REPAIR=1; shift ;;
    --skip-dns-check) SKIP_DNS_CHECK=1; shift ;;
    --plan) PLAN_ONLY=1; shift ;;
    *) die "Unknown option: $1" ;;
  esac
done

prompt_value MAIL_DOMAIN "Mail domain (example.com)"
MAIL_DOMAIN=${MAIL_DOMAIN,,}
APP_HOSTNAME=${APP_HOSTNAME:-app.$MAIL_DOMAIN}
MAIL_HOSTNAME=${MAIL_HOSTNAME:-mail.$MAIL_DOMAIN}
PUBLIC_HOSTNAME=${PUBLIC_HOSTNAME:-$MAIL_DOMAIN}
APP_HOSTNAME=${APP_HOSTNAME,,}
MAIL_HOSTNAME=${MAIL_HOSTNAME,,}
PUBLIC_HOSTNAME=${PUBLIC_HOSTNAME,,}
prompt_value ADMIN_EMAIL "Administrator/contact email"
TLS_EMAIL=${TLS_EMAIL:-$ADMIN_EMAIL}
SERVER_IP=${SERVER_IP:-$(hostname -I 2>/dev/null | awk '{print $1}')}

valid_hostname "$MAIL_DOMAIN" || die "Invalid mail domain: $MAIL_DOMAIN"
valid_hostname "$APP_HOSTNAME" || die "Invalid application hostname: $APP_HOSTNAME"
valid_hostname "$MAIL_HOSTNAME" || die "Invalid mail hostname: $MAIL_HOSTNAME"
valid_hostname "$PUBLIC_HOSTNAME" || die "Invalid public hostname: $PUBLIC_HOSTNAME"
[[ "$APP_HOSTNAME" == *".$MAIL_DOMAIN" ]] || die "Application hostname must be below the mail domain"
[[ "$MAIL_HOSTNAME" == *".$MAIL_DOMAIN" ]] || die "Mail hostname must be below the mail domain"
[[ "$APP_HOSTNAME" != "$MAIL_HOSTNAME" ]] || die "Application and mail hostnames must be different"
[[ "$PUBLIC_HOSTNAME" != "$APP_HOSTNAME" && "$PUBLIC_HOSTNAME" != "$MAIL_HOSTNAME" ]] \
  || die "Public, application, and mail hostnames must be different"
valid_email "$ADMIN_EMAIL" || die "Invalid administrator email"
valid_email "$TLS_EMAIL" || die "Invalid TLS account email"
[[ "$ADMIN_USERNAME" =~ ^[A-Za-z0-9_.@+-]{1,150}$ ]] || die "Invalid administrator username"
if [[ -n "$ADMIN_PASSWORD_ENV" ]]; then
  [[ "$ADMIN_PASSWORD_ENV" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] \
    || die "Invalid administrator password environment variable name"
fi
python3 - "$SERVER_IP" <<'PY' || die "Invalid server IP"
import ipaddress, sys
ipaddress.ip_address(sys.argv[1])
PY

PUBLIC_SERVER_NAMES="$PUBLIC_HOSTNAME"
CERT_DOMAINS=("$PUBLIC_HOSTNAME" "$APP_HOSTNAME" "$MAIL_HOSTNAME")
if (( ENABLE_WWW == 1 )); then
  [[ "$PUBLIC_HOSTNAME" != www.* ]] || die "--www cannot be combined with a public hostname that already starts with www"
  WWW_HOSTNAME="www.$PUBLIC_HOSTNAME"
  valid_hostname "$WWW_HOSTNAME" || die "Invalid www hostname"
  [[ "$WWW_HOSTNAME" != "$APP_HOSTNAME" && "$WWW_HOSTNAME" != "$MAIL_HOSTNAME" ]] \
    || die "The www hostname conflicts with the application or mail hostname"
  PUBLIC_SERVER_NAMES+=" $WWW_HOSTNAME"
  CERT_DOMAINS+=("$WWW_HOSTNAME")
fi
GUNICORN_WORKERS=${VIBMAIL_GUNICORN_WORKERS:-3}
[[ "$GUNICORN_WORKERS" =~ ^[1-9][0-9]?$ ]] || die "VIBMAIL_GUNICORN_WORKERS must be 1-99"
CERT_DOMAIN_DISPLAY=$(IFS=,; printf '%s' "${CERT_DOMAINS[*]}")

cat <<EOF
$PROJECT_NAME $PROJECT_VERSION installation plan
  Mail domain:       $MAIL_DOMAIN
  Application:       https://$APP_HOSTNAME
  Mail server:       $MAIL_HOSTNAME
  Public website:    https://$PUBLIC_HOSTNAME
  Administrator:     $ADMIN_USERNAME
  Contact recipient: $ADMIN_EMAIL
  Server IP:         $SERVER_IP
  TLS certificate:   $CERT_NAME ($CERT_DOMAIN_DISPLAY)
  Mode:              $([[ $REPAIR -eq 1 ]] && printf repair || printf clean-install)
  DNS preflight:     $([[ $SKIP_DNS_CHECK -eq 1 ]] && printf skipped || printf required)
EOF

if (( PLAN_ONLY == 1 )); then
  printf 'PLAN_VALIDATION=PASS\n'
  exit 0
fi

[[ ${EUID:-$(id -u)} -eq 0 ]] || die "Run this installer as root"
trap on_error ERR
[[ -r /etc/os-release ]] || die "Cannot identify the operating system"
# shellcheck disable=SC1091
source /etc/os-release
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 24.04* ]] \
  || die "Ubuntu Server 24.04 LTS is required; found ${ID:-unknown} ${VERSION_ID:-unknown}"

for required_path in mailbox-app public-site scripts deployment/templates; do
  [[ -e "$SOURCE_ROOT/$required_path" ]] || die "Source package is incomplete: $required_path"
done

install -d -m 0750 /var/log
exec 9>"$LOCK_FILE"
flock -n 9 || die "Another MailStack installation is running"
touch "$LOG_FILE"
chmod 0600 "$LOG_FILE"

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_ROOT="/var/backups/vibmail-installer/$STAMP"
install -d -m 0700 "$BACKUP_ROOT"

if [[ -e "$MARKER_FILE" && $REPAIR -eq 0 ]]; then
  die "An installation marker already exists. Use --repair after reviewing the existing deployment."
fi
if [[ $REPAIR -eq 1 && ! -r "$SECRETS_FILE" ]]; then
  die "Repair mode requires $SECRETS_FILE"
fi
if [[ $REPAIR -eq 1 && -r "$MARKER_FILE" ]]; then
  python3 - "$MARKER_FILE" "$MAIL_DOMAIN" "$APP_HOSTNAME" "$MAIL_HOSTNAME" "$PUBLIC_HOSTNAME" <<'PY'
import json
import pathlib
import sys

marker = pathlib.Path(sys.argv[1])
expected = {
    "mail_domain": sys.argv[2],
    "app_hostname": sys.argv[3],
    "mail_hostname": sys.argv[4],
    "public_hostname": sys.argv[5],
}
data = json.loads(marker.read_text(encoding="utf-8"))
for key, value in expected.items():
    if data.get(key) != value:
        raise SystemExit(
            f"repair parameter mismatch for {key}: installed={data.get(key)!r}, requested={value!r}"
        )
PY
fi

CURRENT_PHASE="operating-system-dependencies"
export DEBIAN_FRONTEND=noninteractive
if command -v debconf-set-selections >/dev/null 2>&1; then
  printf '%s\n' \
    "postfix postfix/main_mailer_type select Internet Site" \
    "postfix postfix/mailname string $MAIL_DOMAIN" \
    | debconf-set-selections
fi
log "Installing operating-system dependencies"
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates curl openssl rsync jq sqlite3 dnsutils \
  python3.12 python3.12-venv python3.12-dev python3-pip \
  build-essential pkg-config default-libmysqlclient-dev \
  mariadb-server mariadb-client \
  nginx certbot python3-certbot-nginx \
  postfix postfix-mysql \
  dovecot-core dovecot-lmtpd

systemctl stop postfix dovecot 2>/dev/null || true

require_command python3
require_command python3.12
require_command mariadb
require_command postconf
require_command dovecot
require_command nginx
require_command certbot
require_command rsync
require_command openssl
require_command dig

if (( SKIP_DNS_CHECK == 0 )); then
  CURRENT_PHASE="dns-preflight"
  log "Validating DNS and MX prerequisites"
  python3 - "$PUBLIC_HOSTNAME" "$APP_HOSTNAME" "$MAIL_HOSTNAME" "$SERVER_IP" <<'PY'
import ipaddress
import socket
import sys

public_host, app_host, mail_host, expected_ip_text = sys.argv[1:]
expected_ip = ipaddress.ip_address(expected_ip_text)
for hostname in (public_host, app_host, mail_host):
    try:
        resolved = {
            ipaddress.ip_address(item[4][0])
            for item in socket.getaddrinfo(hostname, 0, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise SystemExit(f"DNS lookup failed for {hostname}: {exc}") from exc
    if not resolved:
        raise SystemExit(f"DNS returned no address for {hostname}")
    if hostname == mail_host and expected_ip not in resolved:
        formatted = ", ".join(sorted(str(address) for address in resolved))
        raise SystemExit(
            f"mail hostname {mail_host} must resolve directly to {expected_ip}; found {formatted}"
        )
PY
  mapfile -t MX_TARGETS < <(
    dig +short MX "$MAIL_DOMAIN" \
      | awk '{print tolower($2)}' \
      | sed 's/\.$//' \
      | sort -u
  )
  printf '%s\n' "${MX_TARGETS[@]}" | grep -Fx -- "$MAIL_HOSTNAME" >/dev/null \
    || die "MX for $MAIL_DOMAIN must include $MAIL_HOSTNAME"
fi

CURRENT_PHASE="service-identities"
log "Creating least-privilege service identities"
if getent group vmail >/dev/null; then
  [[ $(getent group vmail | cut -d: -f3) == 5000 ]] || die "Existing vmail group does not use GID 5000"
else
  groupadd --system --gid 5000 vmail
fi
if id vmail >/dev/null 2>&1; then
  [[ $(id -u vmail) == 5000 ]] || die "Existing vmail user does not use UID 5000"
else
  useradd --system --uid 5000 --gid vmail --home-dir /var/vmail --no-create-home --shell /usr/sbin/nologin vmail
fi
if ! id vibmail-contact >/dev/null 2>&1; then
  useradd --system --gid www-data --home-dir /nonexistent --no-create-home --shell /usr/sbin/nologin vibmail-contact
fi
usermod -a -G postdrop vibmail-contact

install -d -o root -g vmail -m 0750 /opt/vibmail /etc/vibmail
install -d -o vmail -g vmail -m 0750 \
  /var/vmail "/var/vmail/$MAIL_DOMAIN"
install -d -o vmail -g www-data -m 0755 /var/lib/vibmail/static
install -d -o vmail -g vmail -m 0700 /var/lib/vibmail/attachments
install -d -o vmail -g adm -m 0750 /var/log/vibmail
install -d -o root -g www-data -m 0755 /var/www/letsencrypt/.well-known/acme-challenge
install -d -o root -g root -m 0755 /opt/vibmail-public-site/releases
install -d -o root -g www-data -m 0755 "/var/www/$PUBLIC_HOSTNAME"
install -d -o root -g root -m 0750 /etc/vibmail-public-contact

CURRENT_PHASE="secret-provisioning"
if [[ $REPAIR -eq 1 ]]; then
  # shellcheck disable=SC1090
  source "$SECRETS_FILE"
else
  APP_DB_PASSWORD=$(random_hex 32)
  POSTFIX_DB_PASSWORD=$(random_hex 32)
  DJANGO_SECRET_KEY=$(random_hex 48)
  CONTACT_HASH_SECRET=$(random_hex 48)
  cat > "$SECRETS_FILE" <<EOF
APP_DB_PASSWORD='$APP_DB_PASSWORD'
POSTFIX_DB_PASSWORD='$POSTFIX_DB_PASSWORD'
DJANGO_SECRET_KEY='$DJANGO_SECRET_KEY'
CONTACT_HASH_SECRET='$CONTACT_HASH_SECRET'
EOF
  chown root:root "$SECRETS_FILE"
  chmod 0600 "$SECRETS_FILE"
fi
export MAIL_DOMAIN APP_HOSTNAME MAIL_HOSTNAME PUBLIC_HOSTNAME PUBLIC_SERVER_NAMES
export ADMIN_EMAIL SERVER_IP CERT_NAME MAIL_DB_NAME APP_DB_NAME APP_DB_USER POSTFIX_DB_USER
export APP_DB_PASSWORD POSTFIX_DB_PASSWORD DJANGO_SECRET_KEY CONTACT_HASH_SECRET GUNICORN_WORKERS

CURRENT_PHASE="mariadb-provisioning"
log "Provisioning MariaDB schemas and least-privilege users"
systemctl enable --now mariadb
SQL_FILE=$(mktemp /root/vibmail-bootstrap.XXXXXX.sql)
trap 'rm -f -- "${SQL_FILE:-}"' EXIT
render mariadb/bootstrap.sql.tpl "$SQL_FILE" 0600
mariadb --protocol=socket < "$SQL_FILE"
rm -f -- "$SQL_FILE"
SQL_FILE=""

CURRENT_PHASE="application-install"
log "Installing application source and Python dependencies"
rsync -a --delete --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
  "$SOURCE_ROOT/mailbox-app/" /opt/vibmail/app/
chown -R root:vmail /opt/vibmail/app
find /opt/vibmail/app -type d -exec chmod 0750 {} +
find /opt/vibmail/app -type f -exec chmod 0640 {} +
find /opt/vibmail/app/scripts -type f -name '*.sh' -exec chmod 0750 {} +
install -o root -g root -m 0644 \
  /opt/vibmail/app/deployment/logrotate/vibmail /etc/logrotate.d/vibmail

if [[ ! -x /opt/vibmail/venv/bin/python ]]; then
  python3.12 -m venv /opt/vibmail/venv
fi
PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INPUT=1 \
  /opt/vibmail/venv/bin/pip install --requirement /opt/vibmail/app/requirements/production.txt
/opt/vibmail/venv/bin/python -m pip check
chown -R root:vmail /opt/vibmail/venv
chmod -R g+rX,o-rwx /opt/vibmail/venv

render env/vibmail.env.tpl /etc/vibmail/vibmail.env 0640
chown root:vmail /etc/vibmail/vibmail.env

CURRENT_PHASE="public-site-install"
log "Installing public website and contact service"
PUBLIC_RELEASE="/opt/vibmail-public-site/releases/$STAMP"
install -d -o root -g root -m 0755 "$PUBLIC_RELEASE"
rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' \
  "$SOURCE_ROOT/public-site/" "$PUBLIC_RELEASE/"
python3 "$SOURCE_ROOT/scripts/render_public_site.py" \
  "$SOURCE_ROOT/public-site/site-template" "$PUBLIC_RELEASE/site" \
  --public-hostname "$PUBLIC_HOSTNAME" --app-hostname "$APP_HOSTNAME" \
  --mail-hostname "$MAIL_HOSTNAME" --mail-domain "$MAIL_DOMAIN"
ln -sfn "$PUBLIC_RELEASE" /opt/vibmail-public-site/current
ln -sfn /opt/vibmail-public-site/current/site "/var/www/$PUBLIC_HOSTNAME/current"

if [[ ! -x /opt/vibmail-public-site/venv/bin/python ]]; then
  python3.12 -m venv /opt/vibmail-public-site/venv
fi
PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INPUT=1 \
  /opt/vibmail-public-site/venv/bin/pip install --requirement "$PUBLIC_RELEASE/requirements.txt"
/opt/vibmail-public-site/venv/bin/python -m pip check
chmod -R a+rX /opt/vibmail-public-site/venv "$PUBLIC_RELEASE"
render env/contact.env.tpl /etc/vibmail-public-contact/contact.env 0600
chown root:root /etc/vibmail-public-contact/contact.env

CURRENT_PHASE="systemd-install"
log "Installing systemd services"
render systemd/vibmail-gunicorn.service.tpl /etc/systemd/system/vibmail-gunicorn.service 0644
render systemd/vibmail-ingestion.service.tpl /etc/systemd/system/vibmail-ingestion.service 0644
render systemd/vibmail-public-contact.service.tpl /etc/systemd/system/vibmail-public-contact.service 0644
systemctl daemon-reload

CURRENT_PHASE="django-migrations"
log "Applying Django database migrations and static assets"
run_as_vmail /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py migrate --noinput
run_as_vmail /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py verify_mailserver_schema
run_as_vmail /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py sync_mailserver_mailboxes --strict
run_as_vmail /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py verify_mail_storage
run_as_vmail /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py collectstatic --noinput
chown -R vmail:www-data /var/lib/vibmail/static
find /var/lib/vibmail/static -type d -exec chmod 0755 {} +
find /var/lib/vibmail/static -type f -exec chmod 0644 {} +
run_as_vmail /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py check --deploy

if [[ $REPAIR -eq 0 ]]; then
  if [[ -n "$ADMIN_PASSWORD_ENV" ]]; then
    ADMIN_PASSWORD=${!ADMIN_PASSWORD_ENV:-}
    [[ -n "$ADMIN_PASSWORD" ]] || die "Environment variable $ADMIN_PASSWORD_ENV is empty"
  else
    ADMIN_PASSWORD="Vm!$(random_hex 12)"
  fi
  export VIBMAIL_INITIAL_ADMIN_PASSWORD="$ADMIN_PASSWORD"
  run_as_vmail env VIBMAIL_INITIAL_ADMIN_PASSWORD="$ADMIN_PASSWORD" \
    /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py create_initial_admin \
    --username "$ADMIN_USERNAME" --password-env VIBMAIL_INITIAL_ADMIN_PASSWORD
  unset VIBMAIL_INITIAL_ADMIN_PASSWORD
  for system_mailbox in postmaster abuse; do
    run_as_vmail /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py create_system_mailbox \
      "$system_mailbox" --confirm
  done
fi

CURRENT_PHASE="nginx-bootstrap"
log "Installing bootstrap Nginx configuration"
backup_file /etc/nginx/sites-available/vibmail-bootstrap.conf
render nginx/bootstrap.conf.tpl /etc/nginx/sites-available/vibmail-bootstrap.conf 0644
ln -sfn /etc/nginx/sites-available/vibmail-bootstrap.conf /etc/nginx/sites-enabled/vibmail-bootstrap.conf
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable --now nginx
systemctl reload nginx

CURRENT_PHASE="tls-certificate"
log "Obtaining Let's Encrypt certificate"
CERTBOT_ARGS=()
for host in "${CERT_DOMAINS[@]}"; do CERTBOT_ARGS+=(-d "$host"); done
certbot certonly --webroot --webroot-path /var/www/letsencrypt \
  --cert-name "$CERT_NAME" --email "$TLS_EMAIL" --agree-tos --no-eff-email \
  --non-interactive --keep-until-expiring "${CERTBOT_ARGS[@]}"
[[ -r "/etc/letsencrypt/live/$CERT_NAME/fullchain.pem" ]] || die "TLS certificate was not created"

CURRENT_PHASE="mail-stack-configuration"
log "Configuring Postfix and Dovecot receive-only mail flow"
for map in domains mailboxes aliases; do
  render "postfix/mysql-virtual-$map.cf.tpl" "/etc/postfix/mysql-virtual-$map.cf" 0640
  chown root:postfix "/etc/postfix/mysql-virtual-$map.cf"
done
backup_file /etc/postfix/main.cf
backup_file /etc/postfix/master.cf
postconf -e "myhostname = $MAIL_HOSTNAME"
postconf -e "mydomain = $MAIL_DOMAIN"
postconf -e 'myorigin = $myhostname'
postconf -e 'mydestination = localhost'
postconf -e 'inet_interfaces = all'
postconf -e 'inet_protocols = all'
postconf -e 'smtpd_banner = $myhostname ESMTP'
postconf -e 'disable_vrfy_command = yes'
postconf -e 'smtpd_helo_required = yes'
postconf -e 'smtpd_sasl_auth_enable = no'
postconf -e 'smtpd_relay_restrictions = permit_mynetworks, reject_unauth_destination'
postconf -e 'smtpd_recipient_restrictions = reject_unauth_destination'
postconf -e 'virtual_mailbox_domains = mysql:/etc/postfix/mysql-virtual-domains.cf'
postconf -e 'virtual_mailbox_maps = mysql:/etc/postfix/mysql-virtual-mailboxes.cf'
postconf -e 'virtual_alias_maps = mysql:/etc/postfix/mysql-virtual-aliases.cf'
postconf -e 'virtual_mailbox_base = /var/vmail'
postconf -e 'virtual_uid_maps = static:5000'
postconf -e 'virtual_gid_maps = static:5000'
postconf -e 'virtual_minimum_uid = 5000'
postconf -e 'virtual_transport = lmtp:unix:private/dovecot-lmtp'
postconf -e 'message_size_limit = 26214400'
postconf -e 'mailbox_size_limit = 0'
postconf -e "smtpd_tls_cert_file = /etc/letsencrypt/live/$CERT_NAME/fullchain.pem"
postconf -e "smtpd_tls_key_file = /etc/letsencrypt/live/$CERT_NAME/privkey.pem"
postconf -e 'smtpd_tls_security_level = may'
postconf -e 'smtp_tls_security_level = may'
for service in submission submissions smtps; do
  if postconf -M 2>/dev/null | grep -q "^${service}/inet"; then
    postconf -M "${service}/inet="
  fi
done
render dovecot/99-vibmail.conf.tpl /etc/dovecot/conf.d/99-vibmail.conf 0644
postfix check
doveconf -n >/dev/null

CURRENT_PHASE="nginx-final"
log "Installing final Nginx configuration"
render nginx/app.conf.tpl /etc/nginx/sites-available/vibmail-app.conf 0644
render nginx/public.conf.tpl /etc/nginx/sites-available/vibmail-public.conf 0644
ln -sfn /etc/nginx/sites-available/vibmail-app.conf /etc/nginx/sites-enabled/vibmail-app.conf
ln -sfn /etc/nginx/sites-available/vibmail-public.conf /etc/nginx/sites-enabled/vibmail-public.conf
rm -f /etc/nginx/sites-enabled/vibmail-bootstrap.conf
nginx -t

install -d -m 0755 /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/vibmail-reload.sh <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
nginx -t
systemctl reload nginx
systemctl reload postfix
systemctl reload dovecot
EOF
chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/vibmail-reload.sh

CURRENT_PHASE="service-start"
log "Starting and enabling services"
systemctl enable --now postfix dovecot vibmail-gunicorn vibmail-ingestion vibmail-public-contact
systemctl reload nginx

CURRENT_PHASE="acceptance-checks"
log "Executing final acceptance checks"
postmap -q "$MAIL_DOMAIN" mysql:/etc/postfix/mysql-virtual-domains.cf | grep -Fx "$MAIL_DOMAIN" >/dev/null
postmap -q "postmaster@$MAIL_DOMAIN" mysql:/etc/postfix/mysql-virtual-mailboxes.cf \
  | grep -Fx "$MAIL_DOMAIN/postmaster/Maildir/" >/dev/null
run_as_vmail /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py verify_postfix_contract
run_as_vmail /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py check --deploy
for service in mariadb postfix dovecot nginx vibmail-gunicorn vibmail-ingestion vibmail-public-contact; do
  systemctl is-active --quiet "$service" || die "Service is not active: $service"
done
curl --fail --silent --show-error --max-time 20 \
  --resolve "$APP_HOSTNAME:443:127.0.0.1" "https://$APP_HOSTNAME/accounts/login/" >/dev/null
curl --fail --silent --show-error --max-time 20 \
  --resolve "$PUBLIC_HOSTNAME:443:127.0.0.1" "https://$PUBLIC_HOSTNAME/" >/dev/null

install -d -m 0750 /etc/vibmail
python3 - "$MARKER_FILE" <<PY
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
data = {
    "product": "$PROJECT_NAME",
    "version": "$PROJECT_VERSION",
    "installed_at_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "mail_domain": "$MAIL_DOMAIN",
    "app_hostname": "$APP_HOSTNAME",
    "mail_hostname": "$MAIL_HOSTNAME",
    "public_hostname": "$PUBLIC_HOSTNAME",
    "certificate_name": "$CERT_NAME",
}
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
path.chmod(0o600)
PY

if [[ $REPAIR -eq 0 ]]; then
  CREDENTIALS_FILE="/root/vibmail-initial-credentials-$STAMP.txt"
  cat > "$CREDENTIALS_FILE" <<EOF
MailStack initial credentials
============================
Application: https://$APP_HOSTNAME
Username: $ADMIN_USERNAME
Password: $ADMIN_PASSWORD
Mail domain: $MAIL_DOMAIN

Change the administrator password immediately after first sign-in.
This file is root-only. Delete it after storing the credential securely.
EOF
  chmod 0600 "$CREDENTIALS_FILE"
else
  CREDENTIALS_FILE="not-created-in-repair-mode"
fi

CURRENT_PHASE="complete"
trap - ERR
log "Installation completed successfully"
cat <<EOF

VIBMAIL_INSTALL=PASS
Application: https://$APP_HOSTNAME
Public site: https://$PUBLIC_HOSTNAME
SMTP host: $MAIL_HOSTNAME
Initial credentials: $CREDENTIALS_FILE
Installer log: $LOG_FILE
EOF
