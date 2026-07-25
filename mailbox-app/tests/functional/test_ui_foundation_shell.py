from __future__ import annotations

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_admin_dashboard_renders_authenticated_application_shell(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("dashboard:index"))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'class="app-shell"' in content
    assert 'class="app-sidebar"' in content
    assert 'class="app-topbar"' in content
    assert 'aria-label="Primary"' in content
    assert 'href="/" aria-current="page"' in content
    assert "User management" in content
    assert 'action="/accounts/logout/" method="post"' in content
    assert "Receive-only mode" in content
    assert "Outbound sending is disabled" in content
    assert 'data-live-url="/messages/live/"' in content


@pytest.mark.django_db
def test_ordinary_user_shell_hides_administrator_navigation(client):
    user = get_user_model().objects.create_user(
        username="team-member",
        password="Secure-Test-Password-2026!",
    )
    client.force_login(user)
    response = client.get(reverse("dashboard:index"))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'class="app-shell"' in content
    assert "Team member" in content
    assert "User management" not in content
    assert reverse("accounts:user_list") not in content


@pytest.mark.django_db
def test_login_uses_unauthenticated_shell_without_private_navigation(client):
    response = client.get(reverse("accounts:login"))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'class="auth-shell"' in content
    assert 'class="app-sidebar"' not in content
    assert 'data-live-url=' not in content
    assert "User management" not in content
    assert "Receive-only mode" not in content


@pytest.mark.django_db
def test_mailbox_and_message_routes_mark_mailboxes_current(client, admin_user, mailbox, message):
    client.force_login(admin_user)
    urls = (
        reverse("mailboxes:list"),
        reverse("messages:inbox", args=[mailbox.uuid]),
        reverse("messages:detail", args=[mailbox.uuid, message.uuid]),
    )

    for url in urls:
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert (
            'href="/mailboxes/" aria-current="page"' in content
            or 'href="/mailboxes/" class="nav-item is-active" aria-current="page"' in content
        )
        assert "Create mailbox</span>" in content


@pytest.mark.django_db
def test_create_mailbox_route_marks_create_navigation_current(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("mailboxes:create"))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'href="/mailboxes/create/" aria-current="page"' in content


def test_foundation_static_assets_and_frozen_tokens_exist():
    root = Path(__file__).resolve().parents[2]
    foundation = root / "static/css/foundation.css"
    logo = root / "static/brand/mailstack-logo.svg"
    icons = root / "static/icons/mailstack-icons.svg"

    assert foundation.is_file()
    assert logo.is_file()
    assert icons.is_file()
    css = foundation.read_text(encoding="utf-8")
    assert "--ui-primary: #0b4ff5;" in css
    assert "@media (max-width: 1199px)" in css
    assert "@media (max-width: 767px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_base_shell_does_not_activate_planned_features():
    root = Path(__file__).resolve().parents[2]
    base = (root / "templates/base.html").read_text(encoding="utf-8")
    prohibited = (
        "settings:",
        "logs:",
        "teams:",
        "domains:",
        ">Compose<",
        ">Reply<",
        ">Forward<",
        ">Sent<",
        ">Drafts<",
        "IMAP",
        "POP3",
        "Sign up",
    )
    for marker in prohibited:
        assert marker not in base
