from __future__ import annotations

from pathlib import Path

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from apps.audit.services import record_audit
from apps.ingestion.parser import sanitize_html
from apps.ingestion.storage import store_attachment
from apps.mailboxes.validators import confined_path
from apps.messages.models import Attachment


@pytest.mark.django_db
def test_csrf_rejects_login_and_state_change(admin_user, mailbox, message):
    csrf_client = Client(enforce_csrf_checks=True)
    response = csrf_client.post(
        reverse("accounts:login"),
        {"username": admin_user.username, "password": "Secure-Test-Password-2026!"},
    )
    assert response.status_code == 403
    csrf_client.force_login(admin_user)
    response = csrf_client.post(
        reverse("messages:mark_state", args=[mailbox.uuid, message.uuid]),
        {"state": "read"},
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_disallowed_host_is_rejected(client):
    response = client.get(reverse("core:live"), HTTP_HOST="evil.invalid")
    assert response.status_code == 400


@pytest.mark.django_db
def test_security_headers_on_normal_and_html_routes(client, admin_user, message):
    client.force_login(admin_user)
    response = client.get(reverse("dashboard:index"))
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response["Content-Security-Policy"]
    assert response["Permissions-Policy"]

    response = client.get(reverse("messages:safe_html", args=[message.uuid]))
    csp = response["Content-Security-Policy"]
    assert "default-src 'none'" in csp
    assert "img-src data:" in csp
    assert "style-src 'unsafe-inline'" in csp
    assert "base-uri 'none'" in csp
    assert "script-src" not in csp
    assert "form-action 'none'" in csp
    assert "navigate-to 'none'" in csp


def test_css_sanitizer_preserves_presentation_without_remote_or_active_css():
    cleaned = sanitize_html(
        "<style>"
        ".safe{color:red;padding:8px;background-image:url(https://tracker.test/a.png);position:fixed}"
        "@import url(https://tracker.test/x.css);"
        "@media screen and (max-width:600px){.safe{width:100%;display:block}}"
        "</style>"
        '<p style="font-weight:700;transform:scale(2);color:expression(alert(1));'
        'width:var(--mail-width);--mail-width:100%;background-image:url(data:image/png;base64,AAAA)">'
        "Safe</p>"
    ).lower()
    assert ".safe{color:red;padding:8px;}" in cleaned
    assert "@media screen and (max-width:600px)" in cleaned
    assert "font-weight:700;" in cleaned
    assert "tracker.test" not in cleaned
    assert "@import" not in cleaned
    assert "background-image" not in cleaned
    assert "position:fixed" not in cleaned
    assert "transform" not in cleaned
    assert "expression(" not in cleaned
    assert "var(" not in cleaned
    assert "--mail-width" not in cleaned
    assert "data:image" not in cleaned


@pytest.mark.django_db
def test_stored_and_reflected_xss_are_escaped(client, admin_user, mailbox, message):
    message.subject = '<img src=x onerror="alert(1)">'
    message.sender_name = "<script>alert(1)</script>"
    message.save(update_fields=["subject", "sender_name"])
    client.force_login(admin_user)
    response = client.get(reverse("messages:detail", args=[mailbox.uuid, message.uuid]))
    body = response.content.decode()
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body

    response = client.get(reverse("messages:inbox", args=[mailbox.uuid]), {"q": "<script>alert(1)</script>"})
    assert "<script>alert(1)</script>" not in response.content.decode()


@pytest.mark.django_db
def test_invalid_read_state_is_denied(client, admin_user, mailbox, message):
    client.force_login(admin_user)
    response = client.post(
        reverse("messages:mark_state", args=[mailbox.uuid, message.uuid]),
        {"state": "delete"},
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_missing_attachment_returns_404_without_path_disclosure(client, admin_user, mailbox, message):
    attachment = Attachment.objects.create(
        message=message,
        original_filename="missing.txt",
        safe_filename="missing.txt",
        stored_filename="missing.bin",
        declared_mime_type="text/plain",
        detected_mime_type="text/plain",
        size_bytes=0,
        sha256="0" * 64,
        storage_relative_path="aa/missing.bin",
    )
    client.force_login(admin_user)
    response = client.get(
        reverse("messages:attachment_download", args=[mailbox.uuid, message.uuid, attachment.uuid])
    )
    assert response.status_code == 404
    assert b"/var/" not in response.content


@pytest.mark.django_db
def test_filename_header_injection_is_neutralized(client, admin_user, mailbox, message):
    stored = store_attachment(b"safe", "evil\r\nX-Evil: yes.txt")
    attachment = Attachment.objects.create(
        message=message,
        original_filename="evil\r\nX-Evil: yes.txt",
        safe_filename=str(stored["safe_filename"]),
        stored_filename=str(stored["stored_filename"]),
        declared_mime_type="text/plain",
        detected_mime_type="text/plain",
        size_bytes=4,
        sha256=str(stored["sha256"]),
        storage_relative_path=str(stored["storage_relative_path"]),
    )
    client.force_login(admin_user)
    response = client.get(
        reverse("messages:attachment_download", args=[mailbox.uuid, message.uuid, attachment.uuid])
    )
    assert response.status_code == 200
    assert "\r" not in response["Content-Disposition"]
    assert "\n" not in response["Content-Disposition"]
    assert "X-Evil" not in response.headers


@pytest.mark.django_db
def test_audit_details_redact_secrets():
    audit = record_audit(
        "security_test",
        details={
            "password": "secret",
            "nested": {"token": "abc", "safe": "value"},
            "items": [{"cookie": "session"}],
        },
    )
    assert audit.details["password"] == "[REDACTED]"
    assert audit.details["nested"]["token"] == "[REDACTED]"
    assert audit.details["nested"]["safe"] == "value"
    assert audit.details["items"][0]["cookie"] == "[REDACTED]"


def test_path_confinement_rejects_absolute_and_parent(settings):
    with pytest.raises(Exception):
        confined_path(settings.MAIL_STORAGE_ROOT, "..", "outside")
    with pytest.raises(Exception):
        confined_path(settings.ATTACHMENT_STORAGE_ROOT, "/etc/passwd")


@pytest.mark.django_db
@override_settings(
    DEBUG=False,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    CSRF_COOKIE_SECURE=True,
)
def test_production_cookie_flags(client, admin_user):
    response = client.post(
        reverse("accounts:login"),
        {"username": admin_user.username, "password": "Secure-Test-Password-2026!"},
    )
    session = response.cookies["sessionid"]
    assert session["secure"] is True
    assert session["httponly"] is True
    assert session["samesite"] == "Lax"


def test_no_prohibited_user_interface_terms_in_templates():
    root = Path(__file__).resolve().parents[2]
    prohibited = ["Compose", "Reply All", "Forward", "Send email", "Campaign", "Drafts", "Sent mail"]
    content = "\n".join(path.read_text(encoding="utf-8") for path in (root / "templates").rglob("*.html"))
    for term in prohibited:
        assert term not in content


@pytest.mark.django_db
def test_client_ip_honors_forwarded_header_only_when_trusted(rf, settings):
    from apps.audit.services import client_ip

    request = rf.get(
        "/",
        REMOTE_ADDR="192.0.2.10",
        HTTP_X_FORWARDED_FOR="198.51.100.15, 203.0.113.2",
    )
    settings.TRUST_PROXY_HEADERS = False
    assert client_ip(request) == "192.0.2.10"
    settings.TRUST_PROXY_HEADERS = True
    assert client_ip(request) == "198.51.100.15"
    request.META["HTTP_X_FORWARDED_FOR"] = "not-an-ip"
    assert client_ip(request) == "192.0.2.10"


@pytest.mark.django_db
def test_audit_redacts_sensitive_substrings_and_tuples():
    audit = record_audit(
        "redaction_test",
        details={
            "database_password": "hidden",
            "api-token-value": "hidden",
            "safe_tuple": ({"session_cookie": "hidden"}, "visible"),
        },
    )
    assert audit is not None
    assert audit.details["database_password"] == "[REDACTED]"
    assert audit.details["api-token-value"] == "[REDACTED]"
    assert audit.details["safe_tuple"][0]["session_cookie"] == "[REDACTED]"
    assert audit.details["safe_tuple"][1] == "visible"


@pytest.mark.django_db
def test_audit_database_failure_does_not_break_request(monkeypatch):
    from django.db import DatabaseError

    from apps.audit.models import AuditLog

    def fail_create(**_kwargs):
        raise DatabaseError("audit store unavailable")

    monkeypatch.setattr(AuditLog.objects, "create", fail_create)
    assert record_audit("failure_resilience", details={"safe": "value"}) is None
