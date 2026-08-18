from __future__ import annotations

from pathlib import Path

import pytest
from django.urls import get_resolver, reverse


@pytest.mark.django_db
def test_required_routes_resolve(client, admin_user, mailbox, message):
    client.force_login(admin_user)
    urls = [
        reverse("dashboard:index"),
        reverse("mailboxes:list"),
        reverse("mailboxes:create"),
        reverse("messages:inbox", args=[mailbox.uuid]),
        reverse("messages:detail", args=[mailbox.uuid, message.uuid]),
        reverse("accounts:user_list"),
        reverse("core:live"),
        reverse("core:ready"),
    ]
    for url in urls:
        assert client.get(url).status_code == 200

    live_response = client.get(
        reverse("messages:live_updates"),
        HTTP_ACCEPT="application/json",
        HTTP_X_MAILSTACK_LIVE_REQUEST="1",
    )
    assert live_response.status_code == 200
    assert live_response["Content-Type"].startswith("application/json")


def test_css_contains_responsive_breakpoints_and_accessibility_rules():
    root = Path(__file__).resolve().parents[2]
    css = (root / "static" / "css" / "app.css").read_text(encoding="utf-8")
    assert "@media(max-width:1000px)" in css
    assert "@media(max-width:760px)" in css
    assert "@media(max-width:430px)" in css
    assert ":focus-visible" in css
    assert ".skip-link" in css
    assert "overflow-wrap:anywhere" in css


def test_templates_have_semantic_and_accessible_controls():
    root = Path(__file__).resolve().parents[2]
    base = (root / "templates" / "base.html").read_text(encoding="utf-8")
    detail = (root / "templates" / "messages" / "detail.html").read_text(encoding="utf-8")
    assert '<main id="main-content"' in base
    assert 'aria-label="Primary"' in base
    assert 'class="skip-link"' in base
    assert 'sandbox=""' in detail
    assert 'referrerpolicy="no-referrer"' in detail
    assert "Not antivirus scanned" in detail
    assert "Plain text" not in detail
    assert "Safe HTML" not in detail
    assert 'class="message-reader"' in detail


def test_url_configuration_has_no_public_admin_or_registration():
    patterns = str(get_resolver().url_patterns)
    assert "admin/" not in patterns
    assert "register" not in patterns.lower()
    assert "password_reset" not in patterns.lower()
