from __future__ import annotations

import ipaddress
import os
import re
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

_HOST_RE = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]+$")


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"Mandatory production setting {name} is missing")
    return value


def validated_host(name: str) -> str:
    value = required(name).lower().rstrip(".")
    if not _HOST_RE.fullmatch(value):
        raise ImproperlyConfigured(f"{name} must be a valid DNS hostname")
    return value


def validated_absolute_path(name: str, *, forbidden: set[str] | None = None) -> Path:
    value = Path(required(name))
    if not value.is_absolute() or str(value) in (forbidden or {"/"}):
        raise ImproperlyConfigured(f"{name} must be a safe absolute path")
    return value


if os.getenv("DB_ENGINE", "").strip().lower() not in {"mariadb", "mysql"}:
    raise ImproperlyConfigured("Production requires DB_ENGINE=mariadb")

SECRET_KEY = required("DJANGO_SECRET_KEY")
if len(SECRET_KEY) < 50 or SECRET_KEY == "development-only-insecure-key":  # nosec B105
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must contain at least 50 high-entropy characters")

DEBUG = False
MAIL_DOMAIN = validated_host("MAIL_DOMAIN")
MAIL_HOSTNAME = validated_host("MAIL_HOSTNAME")
APP_HOSTNAME = validated_host("APP_HOSTNAME")
if not MAIL_HOSTNAME.endswith(f".{MAIL_DOMAIN}") or not APP_HOSTNAME.endswith(f".{MAIL_DOMAIN}"):
    raise ImproperlyConfigured("MAIL_HOSTNAME and APP_HOSTNAME must be subdomains of MAIL_DOMAIN")

try:
    SERVER_IP = str(ipaddress.ip_address(required("SERVER_IP")))
except ValueError as exc:
    raise ImproperlyConfigured("SERVER_IP must be a valid IPv4 or IPv6 address") from exc

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")  # noqa: F405
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")  # noqa: F405
if APP_HOSTNAME not in {host.lower() for host in ALLOWED_HOSTS}:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must include APP_HOSTNAME")
if f"https://{APP_HOSTNAME}" not in {origin.lower() for origin in CSRF_TRUSTED_ORIGINS}:
    raise ImproperlyConfigured("DJANGO_CSRF_TRUSTED_ORIGINS must include the HTTPS application origin")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": required("DB_NAME"),
        "USER": required("DB_USER"),
        "PASSWORD": required("DB_PASSWORD"),
        "HOST": required("DB_HOST"),
        "PORT": required("DB_PORT"),
        "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),  # noqa: F405
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": (
                "SET sql_mode='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,"
                "NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION'"
            ),
            "isolation_level": "read committed",
        },
    }
}
ssl_ca = os.getenv("DB_SSL_CA", "").strip()
if ssl_ca:
    DATABASES["default"]["OPTIONS"]["ssl"] = {"ca": ssl_ca}

MAIL_STORAGE_ROOT = validated_absolute_path("MAIL_STORAGE_ROOT")
ATTACHMENT_STORAGE_ROOT = validated_absolute_path("ATTACHMENT_STORAGE_ROOT")
STATIC_ROOT = validated_absolute_path("STATIC_ROOT")
LOG_DIRECTORY = validated_absolute_path("LOG_DIRECTORY")
MAILBOX_PROVISION_LOCK_ROOT = validated_absolute_path("MAILBOX_PROVISION_LOCK_ROOT")
INGESTION_LOCK_FILE = Path(required("INGESTION_LOCK_FILE"))
if not INGESTION_LOCK_FILE.is_absolute():
    raise ImproperlyConfigured("INGESTION_LOCK_FILE must be an absolute path")

if not MAILSERVER_INTEGRATION_ENABLED:  # noqa: F405
    raise ImproperlyConfigured("MAILSERVER_INTEGRATION_ENABLED=true is required in production")

for name in (
    "MAILSERVER_DB_NAME",
    "MAILSERVER_DOMAIN_TABLE",
    "MAILSERVER_MAILBOX_TABLE",
    "MAILSERVER_ALIAS_TABLE",
    "MAILSERVER_POSTFIX_VIEW",
):
    if not _IDENTIFIER_RE.fullmatch(str(globals()[name])):
        raise ImproperlyConfigured(f"Unsafe SQL identifier configured for {name}")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)  # noqa: F405
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)  # noqa: F405
TRUST_PROXY_HEADERS = env_bool("TRUST_PROXY_HEADERS", True)  # noqa: F405
if TRUST_PROXY_HEADERS:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = False
USE_X_ACCEL_REDIRECT = env_bool("USE_X_ACCEL_REDIRECT", False)
