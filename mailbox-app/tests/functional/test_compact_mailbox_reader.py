from __future__ import annotations

import pytest
from django.urls import reverse


LIVE_HEADERS = {
    "HTTP_ACCEPT": "application/json",
    "HTTP_X_MAILSTACK_LIVE_REQUEST": "1",
}


@pytest.mark.django_db
def test_live_updates_require_background_request_header(client, admin_user):
    client.force_login(admin_user)
    url = reverse("messages:live_updates")

    direct = client.get(url)
    assert direct.status_code == 302
    assert direct.url == reverse("dashboard:index")
    assert not direct.get("Content-Type", "").startswith("application/json")

    background = client.get(url, {"bootstrap": 1}, **LIVE_HEADERS)
    assert background.status_code == 200
    assert background["Content-Type"].startswith("application/json")


@pytest.mark.django_db
def test_compact_inbox_renders_preview_without_legacy_body_tabs(client, admin_user, mailbox, message):
    message.text_body = "Compact preview text for the mailbox row."
    message.save(update_fields=["text_body"])
    client.force_login(admin_user)

    response = client.get(reverse("messages:inbox", args=[mailbox.uuid]))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'class="mailbox-view"' in body
    assert 'class="message-row unread"' in body
    assert "Compact preview text for the mailbox row." in body
    assert "Plain text" not in body
    assert "Safe HTML" not in body


@pytest.mark.django_db
def test_unified_reader_prefers_sanitized_html_and_preserves_sandbox(client, admin_user, mailbox, message):
    client.force_login(admin_user)

    response = client.get(reverse("messages:detail", args=[mailbox.uuid, message.uuid]))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'class="message-reader"' in body
    assert 'class="email-frame unified-email-frame"' in body
    assert 'sandbox=""' in body
    assert 'referrerpolicy="no-referrer"' in body
    assert "Protected rendering" in body
    assert "Plain body" not in body
    assert "Plain text" not in body
    assert "Safe HTML" not in body


@pytest.mark.django_db
def test_plain_only_message_uses_unified_plain_fallback(client, admin_user, mailbox, message):
    message.sanitized_html_body = ""
    message.text_body = "Plain-only fallback content."
    message.save(update_fields=["sanitized_html_body", "text_body"])
    client.force_login(admin_user)

    response = client.get(reverse("messages:detail", args=[mailbox.uuid, message.uuid]))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'class="email-plain-body"' in body
    assert "Plain-only fallback content." in body
    assert "unified-email-frame" not in body


@pytest.mark.django_db
def test_live_payload_uses_html_text_as_preview_when_plain_body_is_missing(
    client, admin_user, message
):
    message.text_body = ""
    message.sanitized_html_body = "<p>Hello <strong>compact</strong> reader</p>"
    message.save(update_fields=["text_body", "sanitized_html_body"])
    client.force_login(admin_user)

    response = client.get(reverse("messages:live_updates"), {"cursor": 0}, **LIVE_HEADERS)
    assert response.status_code == 200
    payload = response.json()
    row = next(item for item in payload["messages"] if item["uuid"] == str(message.uuid))
    assert row["preview"] == "Hello compact reader"
