from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import secrets
import sqlite3
import subprocess  # nosec B404
import time
import uuid
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from email.message import EmailMessage
from email.utils import parseaddr
from http import HTTPStatus
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any
from urllib.parse import quote

LOGGER = logging.getLogger("vibmail_public_contact")
logging.basicConfig(
    level=os.environ.get("CONTACT_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
)

DATABASE_PATH = Path(
    os.environ.get(
        "CONTACT_DATABASE_PATH",
        "/var/lib/vibmail-public-contact/contact.sqlite3",
    )
)
ADMIN_RECIPIENT = os.environ.get(
    "CONTACT_ADMIN_RECIPIENT",
    "admin@example.com",
).strip()
FROM_ADDRESS = os.environ.get(
    "CONTACT_FROM_ADDRESS",
    "MailStack Website <website@example.com>",
).strip()
SENDMAIL_PATH = os.environ.get("CONTACT_SENDMAIL_PATH", "/usr/sbin/sendmail")
HASH_SECRET = os.environ.get("CONTACT_HASH_SECRET", "")
PUBLIC_ORIGIN = os.environ.get("CONTACT_PUBLIC_ORIGIN", "https://example.com").rstrip("/")
PUBLIC_HOSTNAME = PUBLIC_ORIGIN.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]

MAX_BODY_BYTES = 32_768
CSRF_TTL_SECONDS = 1_200
MIN_FORM_AGE_MS = 2_500
MAX_FORM_AGE_MS = 86_400_000

SERVICE_LABELS = {
    "personal": "Personal private mailbox",
    "team": "Team mailbox access",
    "business": "Business mailbox setup",
    "other": "Other mailbox requirement",
}
TEAM_SIZE_VALUES = {"", "1", "2-5", "6-15", "16-50", "51+"}

EMAIL_RE = re.compile(
    r"^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$",
    re.IGNORECASE,
)
PHONE_RE = re.compile(r"^[0-9+().\-\s]{0,40}$")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
HEADER_CONTROL_RE = re.compile(r"[\r\n\x00-\x1f\x7f]")


def _require_configuration() -> None:
    if len(HASH_SECRET) < 32:
        raise RuntimeError("CONTACT_HASH_SECRET must contain at least 32 characters")
    if not ADMIN_RECIPIENT or HEADER_CONTROL_RE.search(ADMIN_RECIPIENT):
        raise RuntimeError("Invalid CONTACT_ADMIN_RECIPIENT")
    if not FROM_ADDRESS or HEADER_CONTROL_RE.search(FROM_ADDRESS):
        raise RuntimeError("Invalid CONTACT_FROM_ADDRESS")


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
        isolation_level=None,
    )
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute("PRAGMA busy_timeout = 10000")
        yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    _require_configuration()

    with _connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS csrf_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_hash TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                used_at INTEGER
            );

            CREATE UNIQUE INDEX IF NOT EXISTS uq_csrf_token_hash
                ON csrf_tokens(token_hash);

            CREATE INDEX IF NOT EXISTS idx_csrf_session_expiry
                ON csrf_tokens(session_hash, expires_at);

            CREATE TABLE IF NOT EXISTS contact_submissions (
                request_id TEXT PRIMARY KEY,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                ip_hash TEXT NOT NULL,
                email_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                work_email TEXT NOT NULL,
                company TEXT NOT NULL,
                phone TEXT NOT NULL,
                service_type TEXT NOT NULL,
                team_size TEXT NOT NULL,
                message TEXT NOT NULL,
                delivery_status TEXT NOT NULL,
                delivery_error TEXT NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_contact_ip_created
                ON contact_submissions(ip_hash, created_at);

            CREATE INDEX IF NOT EXISTS idx_contact_email_created
                ON contact_submissions(email_hash, created_at);

            CREATE INDEX IF NOT EXISTS idx_contact_status_created
                ON contact_submissions(delivery_status, created_at);
            """
        )


def _digest(value: str) -> str:
    return hmac.new(
        HASH_SECRET.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _json_response(
    start_response,
    status: HTTPStatus,
    payload: dict[str, Any],
    extra_headers: Iterable[tuple[str, str]] = (),
):
    body = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
        ("Referrer-Policy", "same-origin"),
        ("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()"),
        ("X-Frame-Options", "DENY"),
    ]
    headers.extend(extra_headers)
    start_response(f"{status.value} {status.phrase}", headers)
    return [body]


def _request_ip(environ: dict[str, Any]) -> str:
    candidate = str(environ.get("HTTP_X_REAL_IP", "")).strip()
    if not candidate:
        candidate = str(environ.get("REMOTE_ADDR", "")).strip()

    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return str(ipaddress.IPv4Address(0))


def _read_json(environ: dict[str, Any]) -> dict[str, Any]:
    content_type = str(environ.get("CONTENT_TYPE", "")).split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise ValueError("Content-Type must be application/json")

    length_text = str(environ.get("CONTENT_LENGTH", "") or "0")
    try:
        content_length = int(length_text)
    except ValueError as exc:
        raise ValueError("Invalid request length") from exc

    if content_length <= 0 or content_length > MAX_BODY_BYTES:
        raise ValueError("Invalid request size")

    raw = environ["wsgi.input"].read(content_length)
    if len(raw) != content_length:
        raise ValueError("Incomplete request body")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid JSON request") from exc

    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")

    return payload


def _cookie_value(environ: dict[str, Any], name: str) -> str:
    cookie = SimpleCookie()
    try:
        cookie.load(str(environ.get("HTTP_COOKIE", "")))
    except Exception:
        return ""

    morsel = cookie.get(name)
    return morsel.value if morsel else ""


def _issue_csrf(start_response):
    now = int(time.time())
    session_value = secrets.token_urlsafe(32)
    token_value = secrets.token_urlsafe(40)

    session_hash = _digest(f"session:{session_value}")
    token_hash = _digest(f"token:{token_value}")

    with _connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "DELETE FROM csrf_tokens WHERE expires_at < ? OR used_at IS NOT NULL",
            (now - 300,),
        )
        connection.execute(
            """
            INSERT INTO csrf_tokens (
                session_hash,
                token_hash,
                created_at,
                expires_at
            ) VALUES (?, ?, ?, ?)
            """,
            (
                session_hash,
                token_hash,
                now,
                now + CSRF_TTL_SECONDS,
            ),
        )
        connection.commit()

    cookie = (
        f"vm_contact_session={quote(session_value, safe='')}; "
        f"Path=/; Max-Age={CSRF_TTL_SECONDS}; "
        "Secure; HttpOnly; SameSite=Strict"
    )

    return _json_response(
        start_response,
        HTTPStatus.OK,
        {
            "token": token_value,
            "expires_in": CSRF_TTL_SECONDS,
        },
        [("Set-Cookie", cookie)],
    )


def _consume_csrf(environ: dict[str, Any]) -> bool:
    session_value = _cookie_value(environ, "vm_contact_session")
    token_value = str(environ.get("HTTP_X_VIBMAIL_CSRF", "")).strip()

    if not session_value or not token_value:
        return False

    session_hash = _digest(f"session:{session_value}")
    token_hash = _digest(f"token:{token_value}")
    now = int(time.time())

    with _connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT id
            FROM csrf_tokens
            WHERE session_hash = ?
              AND token_hash = ?
              AND used_at IS NULL
              AND expires_at >= ?
            LIMIT 1
            """,
            (session_hash, token_hash, now),
        ).fetchone()

        if row is None:
            connection.rollback()
            return False

        connection.execute(
            "UPDATE csrf_tokens SET used_at = ? WHERE id = ?",
            (now, row["id"]),
        )
        connection.commit()

    return True


def _clean_text(
    payload: dict[str, Any],
    field: str,
    minimum: int,
    maximum: int,
    required: bool = True,
) -> tuple[str, str | None]:
    raw = payload.get(field, "")
    if raw is None:
        raw = ""

    if not isinstance(raw, str):
        return "", "Invalid value."

    value = raw.strip()

    if required and not value:
        return "", "This field is required."

    if not value:
        return "", None

    if len(value) < minimum:
        return "", f"Enter at least {minimum} characters."

    if len(value) > maximum:
        return "", f"Enter no more than {maximum} characters."

    if CONTROL_RE.search(value):
        return "", "Unsupported characters were detected."

    return value, None


def _validate(payload: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    errors: dict[str, str] = {}
    cleaned: dict[str, str] = {}

    full_name, error = _clean_text(payload, "full_name", 2, 100)
    if error:
        errors["full_name"] = error
    else:
        cleaned["full_name"] = full_name

    work_email, error = _clean_text(payload, "work_email", 5, 254)
    if error:
        errors["work_email"] = error
    else:
        _, parsed_email = parseaddr(work_email)
        normalized_email = parsed_email.lower()
        if (
            not normalized_email
            or normalized_email != work_email.lower()
            or not EMAIL_RE.fullmatch(normalized_email)
        ):
            errors["work_email"] = "Enter a valid email address."
        else:
            cleaned["work_email"] = normalized_email

    company, error = _clean_text(payload, "company", 1, 120, required=False)
    if error:
        errors["company"] = error
    else:
        cleaned["company"] = company

    phone, error = _clean_text(payload, "phone", 1, 40, required=False)
    if error:
        errors["phone"] = error
    elif phone and not PHONE_RE.fullmatch(phone):
        errors["phone"] = "Enter a valid phone number."
    else:
        cleaned["phone"] = phone

    service_type = payload.get("service_type", "")
    if not isinstance(service_type, str) or service_type not in SERVICE_LABELS:
        errors["service_type"] = "Select a valid mailbox requirement."
    else:
        cleaned["service_type"] = service_type

    team_size = payload.get("team_size", "")
    if not isinstance(team_size, str) or team_size not in TEAM_SIZE_VALUES:
        errors["team_size"] = "Select a valid team size."
    else:
        cleaned["team_size"] = team_size

    message, error = _clean_text(payload, "message", 20, 2_000)
    if error:
        errors["message"] = error
    else:
        cleaned["message"] = message

    if payload.get("consent") is not True:
        errors["consent"] = "Consent is required."

    honeypot = payload.get("website", "")
    if not isinstance(honeypot, str) or honeypot.strip():
        errors["_spam"] = "Submission rejected."

    started_at = payload.get("form_started_at", "")
    try:
        started_ms = int(str(started_at))
    except (TypeError, ValueError):
        errors["_spam"] = "Submission timing was invalid."
    else:
        age_ms = int(time.time() * 1000) - started_ms
        if age_ms < MIN_FORM_AGE_MS or age_ms > MAX_FORM_AGE_MS:
            errors["_spam"] = "Submission timing was invalid."

    return cleaned, errors


def _rate_limit(ip_hash: str, email_hash: str) -> tuple[bool, int]:
    now = int(time.time())

    with _connection() as connection:
        ip_15m = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM contact_submissions
            WHERE ip_hash = ? AND created_at >= ?
            """,
            (ip_hash, now - 900),
        ).fetchone()["total"]

        ip_day = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM contact_submissions
            WHERE ip_hash = ? AND created_at >= ?
            """,
            (ip_hash, now - 86_400),
        ).fetchone()["total"]

        email_hour = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM contact_submissions
            WHERE email_hash = ? AND created_at >= ?
            """,
            (email_hash, now - 3_600),
        ).fetchone()["total"]

    if ip_15m >= 5:
        return False, 900
    if ip_day >= 20:
        return False, 86_400
    if email_hour >= 3:
        return False, 3_600

    return True, 0


def _store_submission(
    request_id: str,
    ip_hash: str,
    email_hash: str,
    cleaned: dict[str, str],
) -> None:
    now = int(time.time())

    with _connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            INSERT INTO contact_submissions (
                request_id,
                created_at,
                updated_at,
                ip_hash,
                email_hash,
                full_name,
                work_email,
                company,
                phone,
                service_type,
                team_size,
                message,
                delivery_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                request_id,
                now,
                now,
                ip_hash,
                email_hash,
                cleaned["full_name"],
                cleaned["work_email"],
                cleaned["company"],
                cleaned["phone"],
                cleaned["service_type"],
                cleaned["team_size"],
                cleaned["message"],
            ),
        )
        connection.commit()


def _update_delivery(
    request_id: str,
    status: str,
    error: str = "",
) -> None:
    safe_error = error[:500]

    with _connection() as connection:
        connection.execute(
            """
            UPDATE contact_submissions
            SET delivery_status = ?,
                delivery_error = ?,
                updated_at = ?
            WHERE request_id = ?
            """,
            (
                status,
                safe_error,
                int(time.time()),
                request_id,
            ),
        )


def _send_notification(
    request_id: str,
    cleaned: dict[str, str],
) -> None:
    service_label = SERVICE_LABELS[cleaned["service_type"]]

    message = EmailMessage()
    message["From"] = FROM_ADDRESS
    message["To"] = ADMIN_RECIPIENT
    message["Reply-To"] = cleaned["work_email"]
    message["Subject"] = (
        f"[MailStack Inquiry] {service_label} — {cleaned['full_name']}"
    )
    message["Message-ID"] = f"<contact-{request_id}@{PUBLIC_HOSTNAME}>"
    message["X-VibMail-Request-ID"] = request_id

    body = "\n".join(
        [
            f"A new inquiry was submitted through {PUBLIC_HOSTNAME}.",
            "",
            f"Request ID: {request_id}",
            f"Name: {cleaned['full_name']}",
            f"Email: {cleaned['work_email']}",
            f"Company: {cleaned['company'] or 'Not provided'}",
            f"Phone: {cleaned['phone'] or 'Not provided'}",
            f"Mailbox requirement: {service_label}",
            f"Expected users: {cleaned['team_size'] or 'Not specified'}",
            "",
            "Message:",
            cleaned["message"],
            "",
            f"Submitted through: {PUBLIC_ORIGIN}/contact/",
        ]
    )
    message.set_content(body, charset="utf-8")

    completed = subprocess.run(  # noqa: S603  # nosec B603
        [SENDMAIL_PATH, "-t", "-oi"],
        input=message.as_bytes(),
        capture_output=True,
        timeout=15,
        check=False,
    )

    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"Sendmail exited with status {completed.returncode}: {stderr}"
        )


def _submit_contact(environ: dict[str, Any], start_response):
    if not _consume_csrf(environ):
        return _json_response(
            start_response,
            HTTPStatus.FORBIDDEN,
            {
                "message": "The form security token expired. Reload the page and try again."
            },
        )

    try:
        payload = _read_json(environ)
    except ValueError:
        return _json_response(
            start_response,
            HTTPStatus.BAD_REQUEST,
            {"message": "The submitted request was invalid."},
        )

    cleaned, errors = _validate(payload)

    if errors:
        public_errors = {
            key: value
            for key, value in errors.items()
            if not key.startswith("_")
        }

        return _json_response(
            start_response,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            {
                "message": (
                    "The submission was rejected."
                    if "_spam" in errors
                    else "Please correct the highlighted fields."
                ),
                "errors": public_errors,
            },
        )

    request_ip = _request_ip(environ)
    ip_hash = _digest(f"ip:{request_ip}")
    email_hash = _digest(f"email:{cleaned['work_email']}")

    allowed, retry_after = _rate_limit(ip_hash, email_hash)
    if not allowed:
        return _json_response(
            start_response,
            HTTPStatus.TOO_MANY_REQUESTS,
            {
                "message": (
                    "Too many inquiries were submitted. "
                    "Please wait before trying again."
                )
            },
            [("Retry-After", str(retry_after))],
        )

    request_id = uuid.uuid4().hex
    _store_submission(request_id, ip_hash, email_hash, cleaned)

    try:
        _send_notification(request_id, cleaned)
    except Exception as exc:
        LOGGER.exception(
            "Contact delivery failed request_id=%s",
            request_id,
        )
        _update_delivery(request_id, "failed", str(exc))

        return _json_response(
            start_response,
            HTTPStatus.SERVICE_UNAVAILABLE,
            {
                "message": (
                    "Your inquiry could not be delivered right now. "
                    "Please try again later."
                )
            },
        )

    _update_delivery(request_id, "sent")
    LOGGER.info(
        "Contact inquiry delivered request_id=%s service=%s",
        request_id,
        cleaned["service_type"],
    )

    return _json_response(
        start_response,
        HTTPStatus.CREATED,
        {
            "message": "Inquiry submitted successfully.",
            "request_id": request_id,
        },
    )


def _health(start_response):
    try:
        with _connection() as connection:
            connection.execute("SELECT 1").fetchone()
    except Exception:
        LOGGER.exception("Contact service health check failed")
        return _json_response(
            start_response,
            HTTPStatus.SERVICE_UNAVAILABLE,
            {"status": "not_ready"},
        )

    return _json_response(
        start_response,
        HTTPStatus.OK,
        {"status": "ready"},
    )


def application(environ: dict[str, Any], start_response):
    try:
        path = str(environ.get("PATH_INFO", ""))
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()

        if path == "/health/" and method == "GET":
            return _health(start_response)

        if path == "/csrf/" and method == "GET":
            return _issue_csrf(start_response)

        if path == "/" and method == "POST":
            return _submit_contact(environ, start_response)

        if path in {"/", "/csrf/", "/health/"}:
            return _json_response(
                start_response,
                HTTPStatus.METHOD_NOT_ALLOWED,
                {"message": "Method not allowed."},
                [("Allow", "POST" if path == "/" else "GET")],
            )

        return _json_response(
            start_response,
            HTTPStatus.NOT_FOUND,
            {"message": "Not found."},
        )
    except Exception:
        LOGGER.exception("Unhandled contact service error")
        return _json_response(
            start_response,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            {"message": "The contact service encountered an error."},
        )


initialize_database()
