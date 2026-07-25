from __future__ import annotations

import io
import json
import os
import re
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest import mock

TEMP_DIRECTORY = tempfile.TemporaryDirectory()
ROOT = Path(TEMP_DIRECTORY.name)

os.environ["CONTACT_DATABASE_PATH"] = str(ROOT / "contact.sqlite3")
os.environ["CONTACT_HASH_SECRET"] = "test-secret-" + ("x" * 64)
os.environ["CONTACT_ADMIN_RECIPIENT"] = "admin@example.com"
os.environ["CONTACT_FROM_ADDRESS"] = "MailStack Website <website@example.com>"

import contact_app


def request(
    method: str,
    path: str,
    payload=None,
    cookie: str = "",
    csrf: str = "",
    ip: str = "203.0.113.10",
):
    body = b""
    content_type = ""

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        content_type = "application/json"

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        "HTTP_COOKIE": cookie,
        "HTTP_X_VIBMAIL_CSRF": csrf,
        "HTTP_X_REAL_IP": ip,
        "REMOTE_ADDR": "127.0.0.1",
    }

    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    response_body = b"".join(contact_app.application(environ, start_response))
    captured["json"] = json.loads(response_body.decode("utf-8"))
    return captured


def csrf_pair():
    response = request("GET", "/csrf/")
    assert response["status"].startswith("200"), response
    token = response["json"]["token"]
    set_cookie = response["headers"]["Set-Cookie"]
    cookie = set_cookie.split(";", 1)[0]
    return cookie, token


def valid_payload(email="client@example.com"):
    return {
        "full_name": "Test User",
        "work_email": email,
        "company": "Example Company",
        "phone": "+880 1700 000000",
        "service_type": "team",
        "team_size": "2-5",
        "message": "We need private team mailbox access for our operations.",
        "consent": True,
        "website": "",
        "form_started_at": str(int(time.time() * 1000) - 5_000),
    }


health = request("GET", "/health/")
assert health["status"].startswith("200"), health
assert health["json"]["status"] == "ready"

csrf_response = request("GET", "/csrf/")
assert csrf_response["status"].startswith("200"), csrf_response
assert "Secure" in csrf_response["headers"]["Set-Cookie"]
assert "HttpOnly" in csrf_response["headers"]["Set-Cookie"]
assert "SameSite=Strict" in csrf_response["headers"]["Set-Cookie"]

missing_csrf = request("POST", "/", valid_payload())
assert missing_csrf["status"].startswith("403"), missing_csrf

cookie, token = csrf_pair()
invalid = valid_payload()
invalid["work_email"] = "not-an-email"
invalid_response = request(
    "POST",
    "/",
    invalid,
    cookie=cookie,
    csrf=token,
)
assert invalid_response["status"].startswith("422"), invalid_response
assert "work_email" in invalid_response["json"]["errors"]

cookie, token = csrf_pair()
spam = valid_payload()
spam["website"] = "https://spam.invalid"
spam_response = request(
    "POST",
    "/",
    spam,
    cookie=cookie,
    csrf=token,
)
assert spam_response["status"].startswith("422"), spam_response

cookie, token = csrf_pair()
too_fast = valid_payload()
too_fast["form_started_at"] = str(int(time.time() * 1000))
too_fast_response = request(
    "POST",
    "/",
    too_fast,
    cookie=cookie,
    csrf=token,
)
assert too_fast_response["status"].startswith("422"), too_fast_response

cookie, token = csrf_pair()
with mock.patch.object(contact_app, "_send_notification") as sender:
    successful = request(
        "POST",
        "/",
        valid_payload(),
        cookie=cookie,
        csrf=token,
    )

assert successful["status"].startswith("201"), successful
assert re.fullmatch(r"[0-9a-f]{32}", successful["json"]["request_id"])
sender.assert_called_once()

reused = request(
    "POST",
    "/",
    valid_payload("another@example.com"),
    cookie=cookie,
    csrf=token,
)
assert reused["status"].startswith("403"), reused

with contact_app._connection() as connection:
    row = connection.execute(
        """
        SELECT delivery_status, work_email, service_type
        FROM contact_submissions
        WHERE request_id = ?
        """,
        (successful["json"]["request_id"],),
    ).fetchone()

assert row is not None
assert row["delivery_status"] == "sent"
assert row["work_email"] == "client@example.com"
assert row["service_type"] == "team"

with contact_app._connection() as closed_connection:
    closed_connection.execute("SELECT 1").fetchone()
try:
    closed_connection.execute("SELECT 1").fetchone()
except sqlite3.ProgrammingError:
    pass
else:
    raise AssertionError("Contact database connection remained open after context exit")

print("CONTACT_SERVICE_TESTS: PASS")
print("TESTED: health, secure cookie, CSRF, validation, honeypot, timing, persistence, one-time token")
