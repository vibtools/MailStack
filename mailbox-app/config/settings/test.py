from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .base import *  # noqa: F403

DEBUG = False
# Isolated test-only value; production settings require an environment secret.
SECRET_KEY = "test-secret-key-not-for-production"  # nosec B105
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False
MAIL_STORAGE_ROOT = Path(
    os.environ.get("TEST_MAIL_STORAGE_ROOT", tempfile.mkdtemp(prefix="vibmail-test-mail-"))
)
ATTACHMENT_STORAGE_ROOT = Path(
    os.environ.get("TEST_ATTACHMENT_STORAGE_ROOT", tempfile.mkdtemp(prefix="vibmail-test-att-"))
)
_lock_directory = Path(tempfile.mkdtemp(prefix="vibmail-test-lock-"))
MAILBOX_PROVISION_LOCK_ROOT = _lock_directory / "mailbox-provision-locks"
MAILBOX_PROVISION_LOCK_TIMEOUT_SECONDS = 1
INGESTION_LOCK_FILE = Path(
    os.environ.get("TEST_INGESTION_LOCK_FILE", str(_lock_directory / "ingestion.lock"))
)
LOG_DIRECTORY = Path(tempfile.mkdtemp(prefix="vibmail-test-log-"))
LOGGING["handlers"]["file"]["filename"] = LOG_DIRECTORY / "application.log"  # noqa: F405
MIDDLEWARE = [
    item
    for item in MIDDLEWARE
    if item != "whitenoise.middleware.WhiteNoiseMiddleware"  # noqa: F405
]
STORAGES = {
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

if os.getenv("TEST_DB_ENGINE") in {"mariadb", "mysql"}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("TEST_DB_NAME", "vibmail_app_test"),
            "USER": os.getenv("TEST_DB_USER", "vibmail_app_test"),
            "PASSWORD": os.getenv("TEST_DB_PASSWORD", ""),
            "HOST": os.getenv("TEST_DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("TEST_DB_PORT", "3306"),
            "CONN_MAX_AGE": 0,
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'",
                "isolation_level": "read committed",
            },
            "TEST": {"NAME": os.getenv("TEST_DATABASE_NAME", "test_vibmail_app")},
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
