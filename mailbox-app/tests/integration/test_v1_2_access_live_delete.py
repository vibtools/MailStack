from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from filelock import FileLock

from apps.audit.models import AuditLog
from apps.ingestion.service import ingest_file
from apps.ingestion.storage import store_attachment
from apps.mailboxes.models import Mailbox, MailboxMembership
from apps.mailboxes.services import ProvisioningError, provision_mailbox
from apps.messages.models import Attachment, Message
from apps.messages.services import recalculate_mailbox_counters


LIVE_HEADERS = {
    "HTTP_ACCEPT": "application/json",
    "HTTP_X_MAILSTACK_LIVE_REQUEST": "1",
}


@pytest.fixture
def ordinary_user(db):
    return get_user_model().objects.create_user(
        username="member",
        password="Member-Secure-Password-2026!",
    )


@pytest.fixture
def assigned_mailbox(mailbox, ordinary_user):
    MailboxMembership.objects.create(user=ordinary_user, mailbox=mailbox)
    return mailbox


@pytest.mark.django_db
def test_policy_is_created_for_every_new_user(ordinary_user):
    policy = ordinary_user.vibmail_access_policy
    assert policy.can_delete_messages is False
    assert policy.can_delete_mailboxes is False


@pytest.mark.django_db
def test_ordinary_user_sees_only_assigned_mailboxes_and_messages(
    client, ordinary_user, assigned_mailbox, message
):
    other = provision_mailbox("private-admin")
    other_message = Message.objects.create(
        mailbox=other,
        source_file_key="new/private",
        source_sha256="b" * 64,
        subject="Private subject",
        parsed_at=timezone.now(),
    )
    client.force_login(ordinary_user)

    response = client.get(reverse("mailboxes:list"))
    assert assigned_mailbox.email_address.encode() in response.content
    assert other.email_address.encode() not in response.content

    response = client.get(reverse("dashboard:index"))
    assert response.context["total_mailboxes"] == 1
    assert response.context["total_messages"] == 1
    assert other_message.subject.encode() not in response.content

    assert client.get(reverse("messages:inbox", args=[other.uuid])).status_code == 404
    assert client.get(reverse("messages:detail", args=[other.uuid, other_message.uuid])).status_code == 404
    assert client.get(reverse("messages:safe_html", args=[other_message.uuid])).status_code == 404


@pytest.mark.django_db
def test_shared_mailbox_is_visible_to_multiple_users(mailbox):
    first = get_user_model().objects.create_user(username="first", password="Strong-Password-First-2026!")
    second = get_user_model().objects.create_user(username="second", password="Strong-Password-Second-2026!")
    MailboxMembership.objects.create(user=first, mailbox=mailbox)
    MailboxMembership.objects.create(user=second, mailbox=mailbox)
    first_client = Client()
    second_client = Client()
    first_client.force_login(first)
    second_client.force_login(second)
    url = reverse("messages:inbox", args=[mailbox.uuid])
    assert first_client.get(url).status_code == 200
    assert second_client.get(url).status_code == 200


@pytest.mark.django_db
def test_ordinary_user_cannot_access_user_management(client, ordinary_user):
    client.force_login(ordinary_user)
    assert client.get(reverse("accounts:user_list")).status_code == 403
    assert client.get(reverse("accounts:user_create")).status_code == 403


@pytest.mark.django_db
def test_admin_creates_edits_and_deletes_user_without_deleting_mailbox(client, admin_user, mailbox):
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_create"),
        {
            "username": "new-member",
            "is_active": "on",
            "password1": "New-Member-Secure-Password-2026!",
            "password2": "New-Member-Secure-Password-2026!",
            "assigned_mailboxes": [mailbox.pk],
            "can_delete_messages": "on",
        },
    )
    assert response.status_code == 302
    user = get_user_model().objects.get(username="new-member")
    assert user.mailbox_memberships.filter(mailbox=mailbox).exists()
    assert user.vibmail_access_policy.can_delete_messages is True
    assert user.is_staff is False

    response = client.post(
        reverse("accounts:user_edit", args=[user.pk]),
        {
            "username": "renamed-member",
            "is_active": "on",
            "assigned_mailboxes": [mailbox.pk],
            "can_delete_mailboxes": "on",
        },
    )
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.username == "renamed-member"
    assert user.vibmail_access_policy.can_delete_mailboxes is True

    response = client.post(reverse("accounts:user_delete", args=[user.pk]))
    assert response.status_code == 302
    assert not get_user_model().objects.filter(pk=user.pk).exists()
    assert Mailbox.objects.filter(pk=mailbox.pk).exists()
    assert AuditLog.objects.filter(action="user_deleted", target_identifier="renamed-member").exists()


@pytest.mark.django_db
def test_user_creation_never_logs_password(client, admin_user):
    client.force_login(admin_user)
    password = "Never-Log-This-Password-2026!"
    client.post(
        reverse("accounts:user_create"),
        {
            "username": "audit-user",
            "is_active": "on",
            "password1": password,
            "password2": password,
        },
    )
    serialized = json.dumps(list(AuditLog.objects.values("details", "target_identifier")))
    assert password not in serialized


@pytest.mark.django_db
def test_user_delete_invalidates_existing_session(admin_user):
    user = get_user_model().objects.create_user(username="session-user", password="Session-Password-2026!")
    member_client = Client()
    assert member_client.login(username=user.username, password="Session-Password-2026!")
    admin_client = Client()
    admin_client.force_login(admin_user)
    admin_client.post(reverse("accounts:user_delete", args=[user.pk]))
    response = member_client.get(reverse("dashboard:index"))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_current_administrator_cannot_delete_itself(client, admin_user):
    client.force_login(admin_user)
    response = client.post(reverse("accounts:user_delete", args=[admin_user.pk]))
    assert response.status_code == 302
    assert get_user_model().objects.filter(pk=admin_user.pk).exists()


@pytest.mark.django_db
def test_ordinary_mailbox_creation_auto_assigns_creator(client, ordinary_user):
    client.force_login(ordinary_user)
    response = client.post(reverse("mailboxes:create"), {"local_part": "member-created"})
    assert response.status_code == 302
    created = Mailbox.objects.get(local_part="member-created")
    assert created.memberships.filter(user=ordinary_user).exists()


@pytest.mark.django_db
def test_admin_can_create_unassigned_and_assigned_mailboxes(client, admin_user, ordinary_user):
    client.force_login(admin_user)
    client.post(reverse("mailboxes:create"), {"local_part": "admin-only"})
    admin_only = Mailbox.objects.get(local_part="admin-only")
    assert not admin_only.memberships.exists()

    client.post(
        reverse("mailboxes:create"),
        {"local_part": "assigned-box", "assigned_users": [ordinary_user.pk]},
    )
    assigned = Mailbox.objects.get(local_part="assigned-box")
    assert assigned.memberships.filter(user=ordinary_user).exists()


@pytest.mark.django_db
def test_case_insensitive_and_deleted_mailbox_addresses_cannot_be_reused(mailbox, admin_user):
    with pytest.raises(IntegrityError), transaction.atomic():
        Mailbox.objects.create(
            local_part="MAILBOX1",
            email_address="mailbox1@example.com",
            maildir_relative_path="vibmail.my/MAILBOX1/Maildir/",
        )
    mailbox.status = Mailbox.Status.DELETED
    mailbox.deleted_at = timezone.now()
    mailbox.deleted_by = admin_user
    mailbox.save(update_fields=["status", "deleted_at", "deleted_by", "updated_at"])
    with pytest.raises(ProvisioningError):
        provision_mailbox("mailbox1")


@pytest.mark.django_db
def test_message_open_auto_reads_once(client, admin_user, mailbox, message):
    mailbox.total_messages = 1
    mailbox.unread_messages = 1
    mailbox.save(update_fields=["total_messages", "unread_messages", "updated_at"])
    client.force_login(admin_user)
    url = reverse("messages:detail", args=[mailbox.uuid, message.uuid])
    assert client.get(url).status_code == 200
    assert client.get(url).status_code == 200
    message.refresh_from_db()
    mailbox.refresh_from_db()
    assert message.is_read is True
    assert mailbox.unread_messages == 0
    assert (
        AuditLog.objects.filter(action="message_auto_read", target_identifier=str(message.uuid)).count() == 1
    )


@pytest.mark.django_db
def test_message_delete_requires_permission_and_is_soft(client, ordinary_user, assigned_mailbox, message):
    recalculate_mailbox_counters(assigned_mailbox)
    client.force_login(ordinary_user)
    url = reverse("messages:delete", args=[assigned_mailbox.uuid, message.uuid])
    assert client.get(url).status_code == 404

    policy = ordinary_user.vibmail_access_policy
    policy.can_delete_messages = True
    policy.save(update_fields=["can_delete_messages", "updated_at"])
    assert client.get(url).status_code == 200
    assert client.post(url).status_code == 302
    message.refresh_from_db()
    assigned_mailbox.refresh_from_db()
    assert message.deleted_at is not None
    assert assigned_mailbox.total_messages == 0
    assert (
        client.get(reverse("messages:detail", args=[assigned_mailbox.uuid, message.uuid])).status_code == 404
    )


@pytest.mark.django_db
def test_deleted_message_is_not_reingested(mailbox, message, settings):
    source = settings.MAIL_STORAGE_ROOT / "vibmail.my" / mailbox.local_part / "Maildir" / "new" / "same"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("Subject: Same\n\nBody", encoding="utf-8")
    message.source_file_key = "new/same"
    message.deleted_at = timezone.now()
    message.save(update_fields=["source_file_key", "deleted_at", "updated_at"])
    assert ingest_file(mailbox, source) == "duplicate"
    assert Message.objects.filter(mailbox=mailbox, source_file_key="new/same").count() == 1


@pytest.mark.django_db
def test_mailbox_delete_requires_permission_and_preserves_data(
    client, ordinary_user, assigned_mailbox, message
):
    client.force_login(ordinary_user)
    url = reverse("mailboxes:delete", args=[assigned_mailbox.uuid])
    assert client.get(url).status_code == 404

    policy = ordinary_user.vibmail_access_policy
    policy.can_delete_mailboxes = True
    policy.save(update_fields=["can_delete_mailboxes", "updated_at"])
    assert client.get(url).status_code == 200
    response = client.post(url, {"confirmation": assigned_mailbox.email_address})
    assert response.status_code == 302
    assigned_mailbox.refresh_from_db()
    assert assigned_mailbox.status == Mailbox.Status.DELETED
    assert assigned_mailbox.deleted_at is not None
    assert Message.objects.filter(pk=message.pk).exists()
    assert client.get(reverse("messages:inbox", args=[assigned_mailbox.uuid])).status_code == 404


@pytest.mark.django_db
def test_ordinary_user_cannot_toggle_mailbox(client, ordinary_user, assigned_mailbox):
    client.force_login(ordinary_user)
    response = client.post(reverse("mailboxes:toggle", args=[assigned_mailbox.uuid]), {"action": "disable"})
    assert response.status_code == 403
    assigned_mailbox.refresh_from_db()
    assert assigned_mailbox.status == Mailbox.Status.ACTIVE


@pytest.mark.django_db
def test_attachment_access_is_scoped(client, ordinary_user, mailbox, message):
    stored = store_attachment(b"secret bytes", "secret.txt")
    attachment = Attachment.objects.create(
        message=message,
        safe_filename="secret.txt",
        stored_filename=str(stored["stored_filename"]),
        size_bytes=int(stored["size_bytes"]),
        sha256=str(stored["sha256"]),
        storage_relative_path=str(stored["storage_relative_path"]),
    )
    client.force_login(ordinary_user)
    url = reverse("messages:attachment_download", args=[mailbox.uuid, message.uuid, attachment.uuid])
    assert client.get(url).status_code == 404
    MailboxMembership.objects.create(user=ordinary_user, mailbox=mailbox)
    assert client.get(url).status_code == 200


@pytest.mark.django_db
def test_live_endpoint_bootstrap_then_returns_new_message(client, ordinary_user, assigned_mailbox):
    client.force_login(ordinary_user)
    url = reverse("messages:live_updates")
    first = client.get(url, {"cursor": 0, "bootstrap": 1}, **LIVE_HEADERS)
    assert first.status_code == 200
    assert first.json()["messages"] == []
    assert "private" in first["Cache-Control"] and "no-store" in first["Cache-Control"]

    created = Message.objects.create(
        mailbox=assigned_mailbox,
        source_file_key="new/live",
        source_sha256="c" * 64,
        sender_address="live@example.test",
        subject="Live arrival",
        received_at=timezone.now(),
        parsed_at=timezone.now(),
    )
    recalculate_mailbox_counters(assigned_mailbox)
    second = client.get(url, {"cursor": first.json()["cursor"]}, **LIVE_HEADERS)
    payload = second.json()
    assert [item["uuid"] for item in payload["messages"]] == [str(created.uuid)]
    assert payload["summary"]["total_unread"] == 1


@pytest.mark.django_db
def test_live_endpoint_never_leaks_unassigned_mailbox(client, ordinary_user, assigned_mailbox):
    private = provision_mailbox("live-private")
    visible = Message.objects.create(
        mailbox=assigned_mailbox,
        source_file_key="new/visible-live",
        source_sha256="d" * 64,
        subject="Visible live",
        parsed_at=timezone.now(),
    )
    Message.objects.create(
        mailbox=private,
        source_file_key="new/private-live",
        source_sha256="e" * 64,
        subject="Private live",
        parsed_at=timezone.now(),
    )
    client.force_login(ordinary_user)
    response = client.get(reverse("messages:live_updates"), {"cursor": 0}, **LIVE_HEADERS)
    payload = response.json()
    assert [item["uuid"] for item in payload["messages"]] == [str(visible.uuid)]
    assert all(item["mailbox"] != private.email_address for item in payload["messages"])
    assert all(item["email_address"] != private.email_address for item in payload["mailboxes"])


@pytest.mark.django_db
def test_branding_copy_controls_and_no_password_navigation(client, admin_user, mailbox):
    client.force_login(admin_user)
    response = client.get(reverse("mailboxes:list"))
    assert b"MailStack MVP" not in response.content
    assert b"Authorized team use only" in response.content
    assert b"data-copy-email" in response.content
    assert b"Password" not in response.content
    assert b"User management" in response.content


def test_frontend_contains_live_polling_notifications_and_copy_controls():
    root = Path(__file__).resolve().parents[2]
    javascript = (root / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert 'params.set("bootstrap", "1")' in javascript
    assert '"X-MailStack-Live-Request": "1"' in javascript
    assert "data-tabs" not in javascript
    assert "Notification.requestPermission" in javascript
    assert "BroadcastChannel" in javascript
    assert "navigator.clipboard.writeText" in javascript
    assert "document.hidden" in javascript


def test_nginx_source_contains_verified_live_hotfix():
    root = Path(__file__).resolve().parents[2]
    config = (root / "deployment" / "nginx" / "app.vibmail.my.conf").read_text(encoding="utf-8")
    assert "include proxy_params" not in config
    assert "listen 443 ssl;" in config
    assert "listen [::]:443 ssl;" in config
    assert "listen 443 ssl http2" not in config
    assert "/.well-known/acme-challenge/" in config
    assert config.count("proxy_set_header Host $host;") == 2


@pytest.mark.django_db
def test_usernames_are_case_insensitively_unique(client, admin_user):
    get_user_model().objects.create_user(username="CaseMember", password="Case-Member-Password-2026!")
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_create"),
        {
            "username": "casemember",
            "is_active": "on",
            "password1": "Second-Case-Member-Password-2026!",
            "password2": "Second-Case-Member-Password-2026!",
        },
    )
    assert response.status_code == 200
    assert b"already exists" in response.content
    assert get_user_model().objects.filter(username__iexact="casemember").count() == 1


@pytest.mark.django_db
def test_user_configuration_changes_are_individually_audited(client, admin_user, ordinary_user, mailbox):
    client.force_login(admin_user)
    response = client.post(
        reverse("accounts:user_edit", args=[ordinary_user.pk]),
        {
            "username": ordinary_user.username,
            "is_active": "on",
            "assigned_mailboxes": [mailbox.pk],
            "can_delete_messages": "on",
        },
    )
    assert response.status_code == 302
    assert AuditLog.objects.filter(
        action="mailbox_assignment_added", target_identifier=ordinary_user.username
    ).exists()
    assert AuditLog.objects.filter(
        action="user_delete_permissions_changed", target_identifier=ordinary_user.username
    ).exists()


@pytest.mark.django_db
@override_settings(LIVE_UPDATE_MESSAGE_LIMIT=2, LIVE_UPDATE_MAILBOX_LIMIT=1)
def test_live_endpoint_payload_is_bounded(client, admin_user, mailbox):
    second = provision_mailbox("bounded-second")
    for index in range(3):
        Message.objects.create(
            mailbox=mailbox,
            source_file_key=f"new/bounded-{index}",
            source_sha256=f"{index + 1:064x}",
            subject=f"Bounded {index}",
            parsed_at=timezone.now(),
        )
    client.force_login(admin_user)
    payload = client.get(reverse("messages:live_updates"), {"cursor": 0}, **LIVE_HEADERS).json()
    assert len(payload["messages"]) == 2
    assert payload["has_more"] is True
    assert len(payload["mailboxes"]) == 1
    assert second.pk is not None


@pytest.mark.django_db
def test_pagination_preserves_all_inbox_filters(client, admin_user, mailbox):
    for index in range(31):
        Message.objects.create(
            mailbox=mailbox,
            source_file_key=f"new/page-{index}",
            source_sha256=f"{index + 100:064x}",
            sender_address="filter@example.test",
            subject=f"Filter page {index}",
            has_attachments=True,
            parsed_at=timezone.now(),
        )
    client.force_login(admin_user)
    response = client.get(
        reverse("messages:inbox", args=[mailbox.uuid]),
        {"q": "Filter", "read": "unread", "attachments": "yes"},
    )
    assert response.status_code == 200
    content = response.content.decode()
    assert "q=Filter" in content
    assert "read=unread" in content
    assert "attachments=yes" in content


@pytest.mark.django_db
@override_settings(MAILBOX_PROVISION_LOCK_TIMEOUT_SECONDS=0.05)
def test_mailbox_provisioning_lock_prevents_concurrent_same_address(settings):
    lock_root = Path(settings.MAILBOX_PROVISION_LOCK_ROOT)
    lock_root.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(lock_root / "locked-address.lock"))
    with lock, pytest.raises(ProvisioningError, match="currently being provisioned"):
        provision_mailbox("locked-address")
    assert not Mailbox.objects.filter(local_part="locked-address").exists()


@pytest.mark.django_db
def test_live_endpoint_query_count_does_not_scale_with_mailboxes(client, ordinary_user):
    mailboxes = [
        Mailbox.objects.create(
            local_part=f"perf-{index}",
            email_address=f"perf-{index}@vibmail.my",
            maildir_relative_path=f"vibmail.my/perf-{index}/Maildir/",
        )
        for index in range(30)
    ]
    MailboxMembership.objects.bulk_create(
        [MailboxMembership(user=ordinary_user, mailbox=mailbox) for mailbox in mailboxes]
    )
    client.force_login(ordinary_user)
    with CaptureQueriesContext(connection) as queries:
        response = client.get(reverse("messages:live_updates"), {"cursor": 0, "bootstrap": 1}, **LIVE_HEADERS)
    assert response.status_code == 200
    assert len(queries) <= 12


@pytest.mark.django_db
def test_user_list_query_count_does_not_scale_with_users(client, admin_user):
    user_model = get_user_model()
    user_model.objects.bulk_create([user_model(username=f"listed-{index}") for index in range(40)])
    client.force_login(admin_user)
    with CaptureQueriesContext(connection) as queries:
        response = client.get(reverse("accounts:user_list"))
    assert response.status_code == 200
    assert len(queries) <= 10


@pytest.mark.django_db
@override_settings(LIVE_UPDATE_MAILBOX_LIMIT=1, LIVE_UPDATE_VISIBLE_MAILBOX_LIMIT=2)
def test_live_endpoint_returns_requested_visible_authorized_mailboxes(client, ordinary_user, mailbox):
    hidden = provision_mailbox("visible-hidden")
    visible = provision_mailbox("visible-target")
    MailboxMembership.objects.create(user=ordinary_user, mailbox=visible)
    MailboxMembership.objects.create(user=ordinary_user, mailbox=mailbox)
    client.force_login(ordinary_user)

    payload = client.get(
        reverse("messages:live_updates"),
        {
            "cursor": 0,
            "bootstrap": 1,
            "mailboxes": f"{visible.uuid},{hidden.uuid},not-a-uuid",
        },
        **LIVE_HEADERS,
    ).json()

    assert [row["uuid"] for row in payload["mailboxes"]] == [str(visible.uuid)]
