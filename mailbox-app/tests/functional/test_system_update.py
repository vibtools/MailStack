from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from django.urls import reverse

from apps.dashboard import views


@pytest.mark.django_db
def test_system_update_page_allows_nonce_protected_script(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("dashboard:system_update_page"))
    content = response.content.decode()
    csp = response["Content-Security-Policy"]

    assert response.status_code == 200
    assert 'id="btn-check-update"' in content
    assert 'id="btn-start-update"' in content
    assert 'class="licora-confirm-dialog update-confirm-dialog"' in content
    assert 'class="licora-confirm-dialog update-status-dialog"' in content
    assert 'id="btn-update-confirm">Install Update</button>' in content
    assert 'nonce="' in content
    assert "script-src 'self' 'nonce-" in csp
    assert "style-src 'self' 'nonce-" in csp
    assert "'unsafe-inline'; script-src" in csp


@pytest.mark.django_db
def test_other_pages_do_not_receive_system_update_style_relaxation(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("dashboard:index"))

    assert response.status_code == 200
    assert "style-src 'self' 'unsafe-inline'" not in response["Content-Security-Policy"]


@pytest.mark.django_db
def test_check_update_uses_latest_stable_release_and_source_assets(client, admin_user, monkeypatch):
    client.force_login(admin_user)
    response_body = {
        "tag_name": "v1.3.5.3",
        "draft": False,
        "prerelease": False,
        "body": "Release notes",
        "assets": [
            {
                "name": "mailstack-1.3.5.3-source.zip",
                "browser_download_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/mailstack-1.3.5.3-source.zip",
            },
            {
                "name": "mailstack-1.3.5.3-source.zip.sha256",
                "browser_download_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/mailstack-1.3.5.3-source.zip.sha256",
            },
        ],
    }
    response = MagicMock()
    response.read.return_value = json.dumps(response_body).encode()
    response.__enter__.return_value = response
    monkeypatch.setattr("apps.dashboard.views.urllib.request.urlopen", lambda request, timeout: response)

    result = client.get(reverse("dashboard:check_update"))

    assert result.status_code == 200
    assert result.json()["latest_version"] == "1.3.5.3"
    assert result.json()["archive_url"].endswith("-source.zip")
    assert result.json()["checksum_url"].endswith("-source.zip.sha256")


@pytest.mark.django_db
def test_update_preflight_returns_blocked_when_root_worker_is_missing(client, admin_user, monkeypatch):
    client.force_login(admin_user)
    monkeypatch.setattr(views, "_update_preflight", lambda: {
        "status": "blocked",
        "checks": [{"name": "updater worker installed", "passed": False, "detail": "missing"}],
        "message": "missing",
    })

    result = client.get(reverse("dashboard:update_preflight"))

    assert result.status_code == 200
    assert result.json()["status"] == "blocked"


@pytest.mark.django_db
def test_start_update_blocks_when_preflight_is_not_ready(client, admin_user, tmp_path, monkeypatch):
    client.force_login(admin_user)
    monkeypatch.setattr(views, "UPDATE_STATUS_PATH", tmp_path / "update_status.json")
    monkeypatch.setattr(views, "_update_preflight", lambda: {
        "status": "blocked",
        "checks": [],
        "message": "root worker missing",
    })

    result = client.post(
        reverse("dashboard:start_update"),
        data=json.dumps({
            "archive_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/mailstack-1.3.5.3-source.zip",
            "checksum_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/mailstack-1.3.5.3-source.zip.sha256",
        }),
        content_type="application/json",
    )

    assert result.status_code == 503
    assert result.json()["preflight"]["message"] == "root worker missing"


@pytest.mark.django_db
def test_start_update_rejects_existing_active_job(client, admin_user, tmp_path, monkeypatch):
    client.force_login(admin_user)
    status_path = tmp_path / "update_status.json"
    status_path.write_text(json.dumps({"step": "download", "progress": 5}), encoding="utf-8")
    monkeypatch.setattr(views, "UPDATE_STATUS_PATH", status_path)

    result = client.post(
        reverse("dashboard:start_update"),
        data=json.dumps(
            {
                "archive_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/mailstack-1.3.5.3-source.zip",
                "checksum_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/mailstack-1.3.5.3-source.zip.sha256",
            }
        ),
        content_type="application/json",
    )

    assert result.status_code == 409
    assert result.json()["error"] == "An update is already in progress."


@pytest.mark.django_db
def test_start_update_rejects_non_official_release_urls(client, admin_user, monkeypatch):
    client.force_login(admin_user)

    result = client.post(
        reverse("dashboard:start_update"),
        data=json.dumps({
            "archive_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/archive.zip?redirect=evil",
            "checksum_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/archive.zip.sha256",
        }),
        content_type="application/json",
    )

    assert result.status_code == 400
    assert "official repository" in result.json()["error"]


@pytest.mark.django_db
def test_start_update_queues_validated_release_request(client, admin_user, tmp_path, monkeypatch):
    client.force_login(admin_user)
    monkeypatch.setattr(views, "UPDATE_STATUS_PATH", tmp_path / "update_status.json")
    monkeypatch.setattr(views, "UPDATE_REQUEST_PATH", tmp_path / "update_request.json")
    monkeypatch.setattr(views, "UPDATE_PROCESSING_PATH", tmp_path / "update_request.processing.json")
    monkeypatch.setattr(views, "_update_preflight", lambda: {
        "status": "ready",
        "checks": [],
        "message": "Updater is ready.",
    })

    result = client.post(
        reverse("dashboard:start_update"),
        data=json.dumps({
            "archive_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/mailstack-1.3.5.3-source.zip",
            "checksum_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/mailstack-1.3.5.3-source.zip.sha256",
        }),
        content_type="application/json",
    )

    assert result.status_code == 200
    assert json.loads((tmp_path / "update_request.json").read_text(encoding="utf-8")) == {
        "archive_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/mailstack-1.3.5.3-source.zip",
        "checksum_url": "https://github.com/vibtools/MailStack/releases/download/v1.3.5.3/mailstack-1.3.5.3-source.zip.sha256",
        "confirm_upgrade": True,
    }
