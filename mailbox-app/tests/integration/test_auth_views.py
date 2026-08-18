from __future__ import annotations

import pytest
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.ingestion.storage import store_attachment
from apps.messages.models import Attachment


@pytest.mark.django_db
def test_private_pages_redirect_when_unauthenticated(client, mailbox, message):
    urls = [
        reverse("dashboard:index"),
        reverse("mailboxes:list"),
        reverse("mailboxes:create"),
        reverse("messages:inbox", args=[mailbox.uuid]),
        reverse("messages:detail", args=[mailbox.uuid, message.uuid]),
        reverse("messages:safe_html", args=[message.uuid]),
    ]
    for url in urls:
        response = client.get(url)
        assert response.status_code == 302
        assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_login_success_audit_and_safe_next(client, admin_user):
    login_url = reverse("accounts:login")
    response = client.post(
        f"{login_url}?next={reverse('mailboxes:list')}",
        {"username": admin_user.username, "password": "Secure-Test-Password-2026!"},
    )
    assert response.status_code == 302
    assert response.url == reverse("mailboxes:list")
    assert AuditLog.objects.filter(action="login_success", actor=admin_user).exists()

    client.logout()
    response = client.post(
        f"{login_url}?next=https://evil.test/phish",
        {"username": admin_user.username, "password": "Secure-Test-Password-2026!"},
    )
    assert response.url == reverse("dashboard:index")


@pytest.mark.django_db
def test_login_failure_and_rate_limit(client, admin_user, settings):
    settings.LOGIN_FAILURE_LIMIT = 2
    url = reverse("accounts:login")
    for _index in range(2):
        response = client.post(url, {"username": admin_user.username, "password": "wrong"})
        assert response.status_code == 200
    response = client.post(
        url,
        {"username": admin_user.username, "password": "Secure-Test-Password-2026!"},
    )
    assert response.status_code == 200
    assert b"Too many failed attempts" in response.content
    assert AuditLog.objects.filter(action="login_failure").count() == 3


@pytest.mark.django_db
def test_authenticated_user_visiting_login_is_redirected(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("accounts:login"))
    assert response.status_code == 302
    assert response.url == reverse("dashboard:index")


@pytest.mark.django_db
def test_logout_is_post_only_and_audited(client, admin_user):
    client.force_login(admin_user)
    url = reverse("accounts:logout")
    assert client.get(url).status_code == 405
    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse("accounts:login")
    assert AuditLog.objects.filter(action="logout", target_identifier=admin_user.username).exists()


@pytest.mark.django_db
def test_password_change_is_unavailable(client, admin_user):
    client.force_login(admin_user)
    assert client.get("/accounts/password-change/").status_code == 404
    response = client.get(reverse("dashboard:index"))
    assert b"Password" not in response.content


@pytest.mark.django_db
def test_dashboard_empty_and_populated(client, admin_user, mailbox, message):
    client.force_login(admin_user)
    response = client.get(reverse("dashboard:index"))
    assert response.status_code == 200
    assert mailbox.email_address.encode() in response.content
    assert message.subject.encode() in response.content
    assert response.context["total_mailboxes"] == 1
    assert response.context["total_messages"] == 1


@pytest.mark.django_db
def test_mailbox_create_list_search_and_toggle(client, admin_user, settings):
    client.force_login(admin_user)
    response = client.post(reverse("mailboxes:create"), {"local_part": "Sales.Team"})
    assert response.status_code == 302
    mailbox = response.wsgi_request.user  # keeps request evaluated before database assertions
    del mailbox
    from apps.mailboxes.models import Mailbox

    created = Mailbox.objects.get(local_part="sales.team")
    assert created.email_address == "sales.team@vibmail.my"
    assert (settings.MAIL_STORAGE_ROOT / "vibmail.my" / "sales.team" / "Maildir" / "new").is_dir()

    response = client.get(reverse("mailboxes:list"), {"q": "SALES", "status": "active"})
    assert created.email_address.encode() in response.content

    toggle_url = reverse("mailboxes:toggle", args=[created.uuid])
    response = client.post(toggle_url, {"action": "disable"})
    assert response.status_code == 302
    created.refresh_from_db()
    assert created.status == Mailbox.Status.DISABLED
    assert AuditLog.objects.filter(action="mailbox_disable").exists()

    client.post(toggle_url, {"action": "enable"})
    created.refresh_from_db()
    assert created.status == Mailbox.Status.ACTIVE
    assert AuditLog.objects.filter(action="mailbox_enable").exists()

    response = client.post(toggle_url, {"action": "delete"})
    assert response.status_code == 302


@pytest.mark.django_db
def test_mailbox_create_validation_error(client, admin_user):
    client.force_login(admin_user)
    response = client.post(reverse("mailboxes:create"), {"local_part": "../escape"})
    assert response.status_code == 200
    assert (
        b"path separators" in response.content
        or b"lowercase letters" in response.content
        or b"Consecutive dots" in response.content
    )


@pytest.mark.django_db
def test_inbox_search_filters_detail_state_and_safe_html(client, admin_user, mailbox, message):
    client.force_login(admin_user)
    inbox = reverse("messages:inbox", args=[mailbox.uuid])
    response = client.get(inbox, {"q": "Test", "read": "unread", "attachments": "no"})
    assert response.status_code == 200
    assert message.subject.encode() in response.content
    assert AuditLog.objects.filter(action="inbox_access").exists()

    response = client.get(reverse("messages:detail", args=[mailbox.uuid, message.uuid]))
    assert response.status_code == 200
    assert b'class="message-reader"' in response.content
    assert b"Plain text" not in response.content
    assert b"Safe HTML" not in response.content
    assert b'sandbox=""' in response.content
    assert AuditLog.objects.filter(action="message_view").exists()

    html_response = client.get(reverse("messages:safe_html", args=[message.uuid]))
    assert html_response.status_code == 200
    assert b"Safe body" in html_response.content
    assert b"Remote content" not in html_response.content
    assert "default-src 'none'" in html_response["Content-Security-Policy"]
    assert html_response["X-Frame-Options"] == "SAMEORIGIN"

    message.refresh_from_db()
    mailbox.refresh_from_db()
    assert message.is_read is True
    assert mailbox.unread_messages == 0

    state_url = reverse("messages:mark_state", args=[mailbox.uuid, message.uuid])
    state_response = client.post(state_url, {"state": "unread"})
    assert state_response.status_code == 302
    assert state_response.url == reverse("messages:inbox", args=[mailbox.uuid])
    message.refresh_from_db()
    mailbox.refresh_from_db()
    assert message.is_read is False
    assert mailbox.unread_messages == 1


@pytest.mark.django_db
def test_attachment_download_stream_and_x_accel(client, admin_user, mailbox, message, settings):
    stored = store_attachment(b"attachment bytes", "report.txt")
    attachment = Attachment.objects.create(
        message=message,
        original_filename="report.txt",
        safe_filename=str(stored["safe_filename"]),
        stored_filename=str(stored["stored_filename"]),
        declared_mime_type="text/plain",
        detected_mime_type=str(stored["detected_mime_type"]),
        size_bytes=int(stored["size_bytes"]),
        sha256=str(stored["sha256"]),
        storage_relative_path=str(stored["storage_relative_path"]),
    )
    client.force_login(admin_user)
    url = reverse("messages:attachment_download", args=[mailbox.uuid, message.uuid, attachment.uuid])
    response = client.get(url)
    assert response.status_code == 200
    assert b"".join(response.streaming_content) == b"attachment bytes"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert "attachment" in response["Content-Disposition"]
    assert AuditLog.objects.filter(action="attachment_download").exists()

    settings.USE_X_ACCEL_REDIRECT = True
    response = client.get(url)
    assert response.status_code == 200
    assert response["X-Accel-Redirect"].startswith("/_protected_attachments/")


@pytest.mark.django_db
def test_attachment_download_requires_matching_mailbox_and_message(client, admin_user, mailbox, message):
    other = __import__("apps.mailboxes.services", fromlist=["provision_mailbox"]).provision_mailbox("other")
    stored = store_attachment(b"secret", "secret.bin")
    attachment = Attachment.objects.create(
        message=message,
        original_filename="secret.bin",
        safe_filename="secret.bin",
        stored_filename=str(stored["stored_filename"]),
        declared_mime_type="application/octet-stream",
        detected_mime_type="application/octet-stream",
        size_bytes=6,
        sha256=str(stored["sha256"]),
        storage_relative_path=str(stored["storage_relative_path"]),
    )
    client.force_login(admin_user)
    bad_url = reverse("messages:attachment_download", args=[other.uuid, message.uuid, attachment.uuid])
    assert client.get(bad_url).status_code == 404


@pytest.mark.django_db
def test_pagination_for_mailboxes_and_messages(client, admin_user, mailbox):
    from django.utils import timezone

    from apps.mailboxes.models import Mailbox
    from apps.messages.models import Message

    for index in range(30):
        Mailbox.objects.create(
            local_part=f"box{index}",
            email_address=f"box{index}@vibmail.my",
            maildir_relative_path=f"vibmail.my/box{index}/Maildir/",
        )
    for index in range(35):
        Message.objects.create(
            mailbox=mailbox,
            source_file_key=f"new/{index}",
            source_sha256=f"{index:064x}"[-64:],
            subject=f"Message {index}",
            parsed_at=timezone.now(),
        )
    client.force_login(admin_user)
    response = client.get(reverse("mailboxes:list"))
    assert response.context["page_obj"].paginator.num_pages == 2
    response = client.get(reverse("messages:inbox", args=[mailbox.uuid]))
    assert response.context["page_obj"].paginator.num_pages == 2


@pytest.mark.django_db
def test_login_succeeds_after_lockout_expiry_and_clears_failures(client, admin_user, settings):
    from datetime import timedelta

    from django.utils import timezone

    from apps.accounts.models import LoginAttempt

    settings.LOGIN_FAILURE_LIMIT = 2
    settings.LOGIN_FAILURE_WINDOW_SECONDS = 3600
    settings.LOGIN_LOCKOUT_SECONDS = 1
    url = reverse("accounts:login")
    for _index in range(2):
        client.post(url, {"username": admin_user.username, "password": "wrong"})
    LoginAttempt.objects.filter(succeeded=False).update(created_at=timezone.now() - timedelta(seconds=2))

    response = client.post(
        url,
        {"username": admin_user.username, "password": "Secure-Test-Password-2026!"},
    )
    assert response.status_code == 302
    assert response.url == reverse("dashboard:index")
    assert not LoginAttempt.objects.filter(
        username_normalized=admin_user.username.lower(), succeeded=False
    ).exists()
