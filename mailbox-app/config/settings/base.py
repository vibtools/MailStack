from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = Path(os.getenv("VIBMAIL_ENV_FILE", "/etc/vibmail/vibmail.env"))
if ENV_FILE.is_file():
    load_dotenv(ENV_FILE)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "development-only-insecure-key")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")
TRUST_PROXY_HEADERS = env_bool("TRUST_PROXY_HEADERS", False)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.audit",
    "apps.accounts",
    "apps.dashboard",
    "apps.mailboxes",
    "apps.messages",
    "apps.ingestion",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.application_context",
            ],
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()
if DB_ENGINE in {"mariadb", "mysql"}:
    database_options: dict[str, object] = {
        "charset": "utf8mb4",
        "init_command": (
            "SET sql_mode='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,"
            "NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION'"
        ),
        "isolation_level": "read committed",
    }
    ssl_ca = os.getenv("DB_SSL_CA", "").strip()
    if ssl_ca:
        database_options["ssl"] = {"ca": ssl_ca}
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "vibmail_app"),
            "USER": os.getenv("DB_USER", "vibmail_app"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
            "OPTIONS": database_options,
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = Path(os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles")))
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:index"
LOGOUT_REDIRECT_URL = "accounts:login"

MAIL_DOMAIN = os.getenv("MAIL_DOMAIN", "vibmail.my")
MAIL_HOSTNAME = os.getenv("MAIL_HOSTNAME", "mail.vibmail.my")
APP_HOSTNAME = os.getenv("APP_HOSTNAME", "app.vibmail.my")
SOURCE_CODE_URL = os.getenv("SOURCE_CODE_URL", "https://github.com/vibtools/MailStack")
COMPANY_URL = os.getenv("COMPANY_URL", "https://vib.tools/")
OPEN_SOURCE_HUB_URL = os.getenv("OPEN_SOURCE_HUB_URL", "https://dev.vib.tools/")
SUBDOMAIN_SERVICE_URL = os.getenv("SUBDOMAIN_SERVICE_URL", "https://ygit.net/")
SERVER_IP = os.getenv("SERVER_IP", "127.0.0.1")
MAILSERVER_INTEGRATION_ENABLED = env_bool("MAILSERVER_INTEGRATION_ENABLED", False)
MAILSERVER_DB_NAME = os.getenv("MAILSERVER_DB_NAME", "vibmail")
MAILSERVER_DOMAIN_TABLE = os.getenv("MAILSERVER_DOMAIN_TABLE", "mail_domains")
MAILSERVER_MAILBOX_TABLE = os.getenv("MAILSERVER_MAILBOX_TABLE", "mailboxes")
MAILSERVER_ALIAS_TABLE = os.getenv("MAILSERVER_ALIAS_TABLE", "mail_aliases")
MAILSERVER_POSTFIX_VIEW = os.getenv("MAILSERVER_POSTFIX_VIEW", "postfix_virtual_mailboxes")
MAILBOX_DEFAULT_QUOTA_BYTES = env_int("MAILBOX_DEFAULT_QUOTA_BYTES", 2_147_483_648)
MAILBOX_PROVISION_LOCK_ROOT = Path(
    os.getenv("MAILBOX_PROVISION_LOCK_ROOT", str(BASE_DIR / ".runtime" / "mailbox-provision-locks"))
)
MAILBOX_PROVISION_LOCK_TIMEOUT_SECONDS = env_int("MAILBOX_PROVISION_LOCK_TIMEOUT_SECONDS", 15)
MAIL_STORAGE_ROOT = Path(os.getenv("MAIL_STORAGE_ROOT", str(BASE_DIR / ".runtime" / "vmail")))
ATTACHMENT_STORAGE_ROOT = Path(
    os.getenv("ATTACHMENT_STORAGE_ROOT", str(BASE_DIR / ".runtime" / "attachments"))
)
MAX_MESSAGE_SIZE_MB = env_int("MAX_MESSAGE_SIZE_MB", 25)
MAX_ATTACHMENT_SIZE_MB = env_int("MAX_ATTACHMENT_SIZE_MB", 20)
INGESTION_INTERVAL_SECONDS = env_int("INGESTION_INTERVAL_SECONDS", 15)
LIVE_UPDATE_MESSAGE_LIMIT = env_int("LIVE_UPDATE_MESSAGE_LIMIT", 25)
LIVE_UPDATE_MAILBOX_LIMIT = env_int("LIVE_UPDATE_MAILBOX_LIMIT", 250)
LIVE_UPDATE_VISIBLE_MAILBOX_LIMIT = env_int("LIVE_UPDATE_VISIBLE_MAILBOX_LIMIT", 50)
INGESTION_LOCK_FILE = Path(os.getenv("INGESTION_LOCK_FILE", str(BASE_DIR / ".runtime" / "ingestion.lock")))
LOG_DIRECTORY = Path(os.getenv("LOG_DIRECTORY", str(BASE_DIR / ".runtime" / "logs")))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

SESSION_COOKIE_AGE = env_int("SESSION_COOKIE_AGE", 3600)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

LOGIN_FAILURE_LIMIT = env_int("LOGIN_FAILURE_LIMIT", 5)
LOGIN_FAILURE_WINDOW_SECONDS = env_int("LOGIN_FAILURE_WINDOW_SECONDS", 900)
LOGIN_LOCKOUT_SECONDS = env_int("LOGIN_LOCKOUT_SECONDS", 900)

LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "apps.core.logging.JsonFormatter"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "json"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIRECTORY / "application.log",
            "maxBytes": 10_000_000,
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "root": {"handlers": ["console", "file"], "level": LOG_LEVEL},
    "loggers": {
        "django.security.DisallowedHost": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        }
    },
}

SILENCED_SYSTEM_CHECKS: list[str] = []
