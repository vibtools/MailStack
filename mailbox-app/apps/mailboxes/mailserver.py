from __future__ import annotations

import re
import secrets
from dataclasses import dataclass

from django.conf import settings
from django.db import connection


class MailServerContractError(RuntimeError):
    """Raised when the Postfix/Dovecot MariaDB contract is unavailable or inconsistent."""


@dataclass(frozen=True, slots=True)
class MailServerMailbox:
    local_part: str
    email: str
    maildir: str
    active: bool


_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]+$")


def _identifier(value: str, setting_name: str) -> str:
    """Return a backtick-quoted SQL identifier after strict validation."""
    if not _IDENTIFIER_RE.fullmatch(value):
        raise MailServerContractError(f"Unsafe SQL identifier configured for {setting_name}")
    return f"`{value}`"


def _tables() -> dict[str, str]:
    schema = _identifier(str(settings.MAILSERVER_DB_NAME), "MAILSERVER_DB_NAME")
    domain = _identifier(str(settings.MAILSERVER_DOMAIN_TABLE), "MAILSERVER_DOMAIN_TABLE")
    mailbox = _identifier(str(settings.MAILSERVER_MAILBOX_TABLE), "MAILSERVER_MAILBOX_TABLE")
    alias = _identifier(str(settings.MAILSERVER_ALIAS_TABLE), "MAILSERVER_ALIAS_TABLE")
    view = _identifier(str(settings.MAILSERVER_POSTFIX_VIEW), "MAILSERVER_POSTFIX_VIEW")
    return {
        "domains": f"{schema}.{domain}",
        "mailboxes": f"{schema}.{mailbox}",
        "aliases": f"{schema}.{alias}",
        "postfix_view": f"{schema}.{view}",
    }


def integration_enabled() -> bool:
    return bool(settings.MAILSERVER_INTEGRATION_ENABLED)


def _disabled_password_hash() -> str:
    # Deliberately not a valid Dovecot password hash. The random suffix prevents
    # identical values while remaining unrecoverable and unusable for mailbox login.
    return f"!VIBMAIL-READ-ONLY!{secrets.token_urlsafe(48)}"


def list_mailserver_mailboxes() -> list[MailServerMailbox]:
    if not integration_enabled():
        return []
    tables = _tables()
    query = f"""
        SELECT m.local_part, m.email, m.maildir, m.active
        FROM {tables['mailboxes']} AS m
        INNER JOIN {tables['domains']} AS d ON d.id = m.domain_id
        WHERE d.name = %s
        ORDER BY m.email
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [settings.MAIL_DOMAIN])
        return [
            MailServerMailbox(
                local_part=row[0],
                email=row[1],
                maildir=row[2],
                active=bool(row[3]),
            )
            for row in cursor.fetchall()
        ]


def mailserver_mailbox_exists(email: str) -> bool:
    if not integration_enabled():
        return False
    tables = _tables()
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT 1 FROM {tables['mailboxes']} WHERE email = %s LIMIT 1",  # noqa: S608
            [email],
        )
        return cursor.fetchone() is not None


def _alias_source_exists(email: str) -> bool:
    tables = _tables()
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT 1 FROM {tables['aliases']} WHERE source = %s AND active = 1 LIMIT 1",  # noqa: S608
            [email],
        )
        return cursor.fetchone() is not None


def create_mailserver_mailbox(*, local_part: str, email: str, maildir: str) -> None:
    if not integration_enabled():
        return
    if _alias_source_exists(email):
        raise MailServerContractError(f"An active mail alias already uses {email} as its source")
    tables = _tables()
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT id FROM {tables['domains']} WHERE name = %s AND active = 1 LIMIT 1",  # noqa: S608
            [settings.MAIL_DOMAIN],
        )
        row = cursor.fetchone()
        if row is None:
            raise MailServerContractError(f"Active mail domain {settings.MAIL_DOMAIN} is unavailable")
        domain_id = row[0]
        cursor.execute(
            f"SELECT 1 FROM {tables['mailboxes']} WHERE email = %s LIMIT 1",  # noqa: S608
            [email],
        )
        if cursor.fetchone() is not None:
            raise MailServerContractError(f"Mailbox {email} already exists in the mail server")
        cursor.execute(
            f"""
            INSERT INTO {tables['mailboxes']}
                (domain_id, local_part, email, password_hash, maildir, quota_bytes, active)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
            """,
            [
                domain_id,
                local_part,
                email,
                _disabled_password_hash(),
                maildir,
                settings.MAILBOX_DEFAULT_QUOTA_BYTES,
            ],
        )
        if cursor.rowcount != 1:
            raise MailServerContractError(f"Failed to create mail-server mailbox {email}")


def set_mailserver_mailbox_active(*, email: str, active: bool) -> None:
    if not integration_enabled():
        return
    tables = _tables()
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {tables['mailboxes']} SET active = %s WHERE email = %s",  # noqa: S608
            [1 if active else 0, email],
        )
        if cursor.rowcount != 1:
            raise MailServerContractError(f"Mail-server mailbox {email} is missing")


def postfix_rows() -> list[tuple[str, str]]:
    if not integration_enabled():
        with connection.cursor() as cursor:
            cursor.execute("SELECT email, maildir_path FROM postfix_virtual_mailboxes ORDER BY email")
            return [(row[0], row[1]) for row in cursor.fetchall()]
    tables = _tables()
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT email, maildir FROM {tables['postfix_view']} ORDER BY email"  # noqa: S608
        )
        return [(row[0], row[1]) for row in cursor.fetchall()]


def verify_mailserver_schema() -> dict[str, int]:
    if not integration_enabled():
        return {"domains": 0, "mailboxes": 0, "postfix_rows": 0}
    tables = _tables()
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) FROM {tables['domains']} WHERE name = %s AND active = 1",  # noqa: S608
            [settings.MAIL_DOMAIN],
        )
        active_domains = int(cursor.fetchone()[0])
        if active_domains != 1:
            raise MailServerContractError(
                f"Exactly one active {settings.MAIL_DOMAIN} domain record is required"
            )
        cursor.execute(
            f"SELECT COUNT(*) FROM {tables['mailboxes']}"  # noqa: S608
        )
        mailbox_count = int(cursor.fetchone()[0])
        cursor.execute(
            f"SELECT COUNT(*) FROM {tables['postfix_view']}"  # noqa: S608
        )
        postfix_count = int(cursor.fetchone()[0])
    return {"domains": active_domains, "mailboxes": mailbox_count, "postfix_rows": postfix_count}
