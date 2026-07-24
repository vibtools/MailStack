from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.urls import reverse
from filelock import FileLock

from apps.mailboxes.models import Mailbox
from apps.mailboxes.services import mailbox_paths
from apps.messages.models import Message


@pytest.mark.django_db
def test_postfix_view_tracks_active_status(mailbox):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT email, maildir_path FROM postfix_virtual_mailboxes WHERE email = lower(%s)",
            [mailbox.email_address.upper()],
        )
        assert cursor.fetchone() == (mailbox.email_address, mailbox.maildir_relative_path)

    mailbox.status = Mailbox.Status.DISABLED
    mailbox.save(update_fields=["status", "updated_at"])
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT email FROM postfix_virtual_mailboxes WHERE email = %s", [mailbox.email_address]
        )
        assert cursor.fetchone() is None

    mailbox.status = Mailbox.Status.ACTIVE
    mailbox.save(update_fields=["status", "updated_at"])
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT maildir_path FROM postfix_virtual_mailboxes WHERE email = %s", [mailbox.email_address]
        )
        assert cursor.fetchone() == (mailbox.maildir_relative_path,)


@pytest.mark.django_db
def test_postfix_view_excludes_structurally_invalid_active_rows():
    invalid = Mailbox.objects.create(
        local_part="bad..name",
        email_address="bad..name@vibmail.my",
        status=Mailbox.Status.ACTIVE,
        maildir_relative_path="vibmail.my/bad..name/Maildir/",
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT email FROM postfix_virtual_mailboxes WHERE email = %s",
            [invalid.email_address],
        )
        assert cursor.fetchone() is None


@pytest.mark.django_db
def test_verify_postfix_contract_command(mailbox):
    output = StringIO()
    call_command("verify_postfix_contract", stdout=output)
    assert "verified" in output.getvalue().lower()


@pytest.mark.django_db
def test_verify_mail_storage_and_provision_commands(mailbox):
    output = StringIO()
    call_command("verify_mail_storage", stdout=output)
    assert "verified" in output.getvalue().lower()

    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    (maildir / "cur").rmdir()
    with pytest.raises(CommandError):
        call_command("verify_mail_storage")
    call_command("provision_maildirs")
    assert (maildir / "cur").is_dir()


@pytest.mark.django_db
def test_provision_maildirs_unknown_mailbox_fails():
    with pytest.raises(CommandError):
        call_command("provision_maildirs", mailbox="missing")


@pytest.mark.django_db
def test_create_initial_admin_from_environment(monkeypatch):
    monkeypatch.setenv("VIBMAIL_TEST_ADMIN_PASSWORD", "Strong-Initial-Password-2026!")
    output = StringIO()
    call_command(
        "create_initial_admin",
        username="owner",
        password_env="VIBMAIL_TEST_ADMIN_PASSWORD",
        stdout=output,
    )
    user = get_user_model().objects.get(username="owner")
    assert user.is_superuser
    assert user.check_password("Strong-Initial-Password-2026!")
    with pytest.raises(CommandError):
        call_command(
            "create_initial_admin",
            username="second",
            password_env="VIBMAIL_TEST_ADMIN_PASSWORD",
        )


@pytest.mark.django_db
def test_create_system_mailbox_requires_confirmation():
    with pytest.raises(CommandError):
        call_command("create_system_mailbox", "postmaster")
    call_command("create_system_mailbox", "postmaster", confirm=True)
    mailbox = Mailbox.objects.get(local_part="postmaster")
    assert mailbox.email_address == "postmaster@vibmail.my"
    _root, maildir, _relative = mailbox_paths(mailbox.local_part, allow_reserved=True)
    assert (maildir / "new").is_dir()
    call_command("verify_mail_storage")


@pytest.mark.django_db
def test_create_system_mailbox_can_create_ui_reserved_address():
    call_command("create_system_mailbox", "admin", confirm=True)
    assert Mailbox.objects.filter(local_part="admin", status=Mailbox.Status.ACTIVE).exists()


@pytest.mark.django_db
def test_update_mailbox_counters_command(mailbox, message):
    mailbox.total_messages = 99
    mailbox.unread_messages = 99
    mailbox.save(update_fields=["total_messages", "unread_messages"])
    call_command("update_mailbox_counters")
    mailbox.refresh_from_db()
    assert mailbox.total_messages == 1
    assert mailbox.unread_messages == 1


@pytest.mark.django_db
def test_ingestion_management_command_once_and_dry_run(mailbox, fixtures_dir):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    (maildir / "new" / "command").write_bytes((fixtures_dir / "plain_text.eml").read_bytes())
    output = StringIO()
    call_command("ingest_maildir", once=True, stdout=output)
    assert "created=1" in output.getvalue()
    assert Message.objects.count() == 1
    call_command("rebuild_mail_index", mailbox=mailbox.local_part, dry_run=True)


@pytest.mark.django_db
def test_ingestion_command_rejects_bad_interval_and_second_worker(settings):
    with pytest.raises(CommandError):
        call_command("ingest_maildir", once=True, interval=0)
    settings.INGESTION_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(settings.INGESTION_LOCK_FILE))
    lock.acquire(timeout=0)
    try:
        with pytest.raises(CommandError):
            call_command("ingest_maildir", once=True)
    finally:
        lock.release()


@pytest.mark.django_db
def test_health_endpoints(client):
    live = client.get(reverse("core:live"))
    assert live.status_code == 200
    assert live.json() == {"status": "live"}

    ready = client.get(reverse("core:ready"))
    assert ready.status_code == 200
    payload = ready.json()
    assert payload["status"] == "ready"
    assert payload["checks"]["database"]["ok"] is True
    serialized = ready.content.decode()
    assert "password" not in serialized.lower()
    assert "/var/" not in serialized


@pytest.mark.django_db
def test_health_ready_reports_unavailable_storage(client, settings, monkeypatch):
    settings.MAIL_STORAGE_ROOT = Path("/proc/vibmail-impossible")
    response = client.get(reverse("core:ready"))
    assert response.status_code == 503
    assert response.json()["checks"]["mail_storage"]["ok"] is False


@pytest.mark.django_db
def test_service_and_model_strings(mailbox):
    from apps.audit.models import AuditLog
    from apps.core.models import ServiceHeartbeat

    heartbeat = ServiceHeartbeat.objects.create(service_name="maildir_ingestion", status="healthy")
    audit = AuditLog.objects.create(action="test", target_identifier=mailbox.email_address)
    assert str(heartbeat) == "maildir_ingestion: healthy"
    assert str(audit) == f"test {mailbox.email_address}"


@pytest.mark.django_db
def test_ingest_command_accepts_rebuild_missing(mailbox, fixtures_dir):
    from django.core.management import call_command

    from apps.mailboxes.services import mailbox_paths

    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    (maildir / "new" / "rebuild-source").write_bytes((fixtures_dir / "plain_text.eml").read_bytes())
    call_command("ingest_maildir", "--once", "--rebuild-missing", mailbox=mailbox.local_part)
    assert mailbox.messages.filter(source_file_key="new/rebuild-source").exists()
