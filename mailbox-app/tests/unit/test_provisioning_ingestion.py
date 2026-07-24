from __future__ import annotations

import os
from contextlib import suppress
from unittest.mock import patch

import pytest
from django.db import IntegrityError

from apps.audit.models import AuditLog
from apps.ingestion.service import (
    ingest_all,
    ingest_file,
    iter_maildir_files,
    source_key,
    update_mailbox_counters,
)
from apps.mailboxes.models import Mailbox
from apps.mailboxes.services import ProvisioningError, ensure_maildir, mailbox_paths, provision_mailbox
from apps.messages.models import Message


@pytest.mark.django_db
def test_mailbox_paths_and_provisioning(settings):
    mailbox = provision_mailbox("Sales.Team")
    root, maildir, relative = mailbox_paths("sales.team")
    assert root == settings.MAIL_STORAGE_ROOT / "vibmail.my" / "sales.team"
    assert maildir == root / "Maildir"
    assert relative == "vibmail.my/sales.team/Maildir/"
    assert mailbox.email_address == "sales.team@vibmail.my"
    for name in ("new", "cur", "tmp"):
        child = maildir / name
        assert child.is_dir()
        assert child.stat().st_mode & 0o777 == 0o700
    assert AuditLog.objects.filter(action="mailbox_create").exists()


@pytest.mark.django_db
def test_provisioning_rolls_back_new_empty_tree_on_database_failure(settings):
    with (
        patch.object(Mailbox, "save", side_effect=IntegrityError("database failure")),
        pytest.raises(ProvisioningError),
    ):
        provision_mailbox("rollback")
    assert not (settings.MAIL_STORAGE_ROOT / "vibmail.my" / "rollback").exists()
    assert AuditLog.objects.filter(action="mailbox_provisioning_failure").exists()


@pytest.mark.django_db
def test_provisioning_does_not_remove_preexisting_tree_on_database_failure(settings):
    root = settings.MAIL_STORAGE_ROOT / "vibmail.my" / "existing"
    root.mkdir(parents=True)
    marker = root / "preserve.txt"
    marker.write_text("preserve", encoding="utf-8")
    with (
        patch.object(Mailbox, "save", side_effect=IntegrityError("database failure")),
        pytest.raises(ProvisioningError),
    ):
        provision_mailbox("existing")
    assert marker.read_text(encoding="utf-8") == "preserve"
    assert not (root / "Maildir").exists()


@pytest.mark.django_db
def test_provisioning_filesystem_failure_creates_no_mailbox(settings):
    blocked = settings.MAIL_STORAGE_ROOT / "vibmail.my"
    blocked.write_text("not a directory", encoding="utf-8")
    with pytest.raises(ProvisioningError):
        provision_mailbox("failure")
    assert not Mailbox.objects.filter(local_part="failure").exists()


@pytest.mark.django_db
def test_ensure_maildir_is_idempotent(mailbox):
    first = ensure_maildir(mailbox)
    second = ensure_maildir(mailbox)
    assert first == second
    assert all((first / child).is_dir() for child in ("new", "cur", "tmp"))


@pytest.mark.django_db
def test_source_key_rejects_outside_and_tmp(mailbox, tmp_path):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    valid = maildir / "new" / "id"
    valid.write_bytes(b"x")
    assert source_key(mailbox, valid) == "new/id"
    tmp_file = maildir / "tmp" / "id"
    tmp_file.write_bytes(b"x")
    with pytest.raises(ValueError):
        source_key(mailbox, tmp_file)
    outside = tmp_path / "outside"
    outside.write_bytes(b"x")
    with pytest.raises(ValueError):
        source_key(mailbox, outside)


@pytest.mark.django_db
def test_ingest_file_is_idempotent_and_preserves_source(mailbox, fixtures_dir):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    source = maildir / "new" / "delivery-1"
    source.write_bytes((fixtures_dir / "one_attachment.eml").read_bytes())
    assert ingest_file(mailbox, source) == "created"
    assert ingest_file(mailbox, source) == "duplicate"
    assert source.is_file()
    message = Message.objects.get(mailbox=mailbox)
    assert message.subject == "One attachment"
    assert message.attachments.count() == 1
    assert message.has_attachments is True
    mailbox.refresh_from_db()
    assert mailbox.total_messages == 1
    assert mailbox.unread_messages == 1


@pytest.mark.django_db
def test_identical_raw_bytes_under_two_source_keys_are_separate(mailbox, fixtures_dir):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    raw = (fixtures_dir / "identical_delivery_a.eml").read_bytes()
    first = maildir / "new" / "first"
    second = maildir / "new" / "second"
    first.write_bytes(raw)
    second.write_bytes(raw)
    assert ingest_file(mailbox, first) == "created"
    assert ingest_file(mailbox, second) == "created"
    assert Message.objects.filter(mailbox=mailbox).count() == 2
    assert Message.objects.values("source_sha256").distinct().count() == 1


@pytest.mark.django_db
def test_oversized_message_records_status_without_loading_body(mailbox, settings, fixtures_dir):
    settings.MAX_MESSAGE_SIZE_MB = 0
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    source = maildir / "new" / "oversized"
    source.write_bytes((fixtures_dir / "oversized_simulation.eml").read_bytes())
    assert ingest_file(mailbox, source) == "oversized"
    message = Message.objects.get(mailbox=mailbox)
    assert message.parse_status == Message.ParseStatus.OVERSIZED
    assert len(message.source_sha256) == 64
    assert source.exists()


@pytest.mark.django_db
def test_dry_run_does_not_create_records(mailbox, fixtures_dir):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    source = maildir / "cur" / "dry-run"
    source.write_bytes((fixtures_dir / "plain_text.eml").read_bytes())
    assert ingest_file(mailbox, source, dry_run=True) == "created"
    assert Message.objects.count() == 0


@pytest.mark.django_db
def test_iter_maildir_ignores_tmp_and_symlinks(mailbox, fixtures_dir):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    raw = (fixtures_dir / "plain_text.eml").read_bytes()
    (maildir / "new" / "one").write_bytes(raw)
    (maildir / "cur" / "two").write_bytes(raw)
    (maildir / "tmp" / "ignored").write_bytes(raw)
    with suppress(OSError):
        os.symlink(maildir / "new" / "one", maildir / "new" / "linked")
    names = {path.name for path in iter_maildir_files(mailbox)}
    assert names == {"one", "two"}


@pytest.mark.django_db
def test_ingest_all_continues_after_one_file_error(mailbox, fixtures_dir, monkeypatch):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    first = maildir / "new" / "first"
    second = maildir / "new" / "second"
    first.write_bytes((fixtures_dir / "plain_text.eml").read_bytes())
    second.write_bytes((fixtures_dir / "html.eml").read_bytes())
    real = ingest_file

    def fail_first(target_mailbox, path, *, dry_run=False):
        if path.name == "first":
            raise OSError("simulated")
        return real(target_mailbox, path, dry_run=dry_run)

    monkeypatch.setattr("apps.ingestion.service.ingest_file", fail_first)
    result = ingest_all()
    assert result.scanned == 2
    assert result.errors == 1
    assert result.created == 1


@pytest.mark.django_db
def test_update_mailbox_counters(mailbox, message):
    message.is_read = True
    message.save(update_fields=["is_read"])
    update_mailbox_counters(mailbox)
    mailbox.refresh_from_db()
    assert mailbox.total_messages == 1
    assert mailbox.unread_messages == 0
    assert mailbox.last_received_at == message.received_at


@pytest.mark.django_db
def test_attachment_storage_failure_rolls_back_database_and_files(mailbox, fixtures_dir, monkeypatch):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    source = maildir / "new" / "storage-failure"
    source.write_bytes((fixtures_dir / "one_attachment.eml").read_bytes())

    def fail_store(*_args, **_kwargs):
        raise OSError("storage unavailable")

    monkeypatch.setattr("apps.ingestion.service.store_attachment", fail_store)
    with pytest.raises(OSError):
        ingest_file(mailbox, source)
    assert Message.objects.count() == 0
    assert AuditLog.objects.filter(action="ingestion_error").exists()


@pytest.mark.django_db
def test_attachment_over_limit_is_skipped_and_message_retained(mailbox, settings, fixtures_dir):
    settings.MAX_ATTACHMENT_SIZE_MB = 0
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    source = maildir / "new" / "attachment-too-large"
    source.write_bytes((fixtures_dir / "one_attachment.eml").read_bytes())

    assert ingest_file(mailbox, source) == "created"
    message = Message.objects.get(mailbox=mailbox)
    assert message.parse_status == Message.ParseStatus.WARNING
    assert "Attachment skipped" in message.parse_warning
    assert message.has_attachments is False
    assert message.attachments.count() == 0


@pytest.mark.django_db
def test_attachment_database_race_removes_stored_file(mailbox, fixtures_dir, monkeypatch, settings):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    source = maildir / "new" / "attachment-db-race"
    source.write_bytes((fixtures_dir / "one_attachment.eml").read_bytes())

    monkeypatch.setattr(
        "apps.ingestion.service.Attachment.objects.create",
        lambda **_kwargs: (_ for _ in ()).throw(IntegrityError("simulated race")),
    )
    assert ingest_file(mailbox, source) == "duplicate"
    assert Message.objects.count() == 0
    assert not any(settings.ATTACHMENT_STORAGE_ROOT.rglob("*.*"))


@pytest.mark.django_db
def test_second_attachment_storage_failure_cleans_first_file(mailbox, fixtures_dir, monkeypatch, settings):
    from apps.ingestion.storage import store_attachment as real_store

    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    source = maildir / "new" / "partial-storage-failure"
    source.write_bytes((fixtures_dir / "multiple_attachments.eml").read_bytes())
    calls = 0

    def fail_second(content, original_filename):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("second write failed")
        return real_store(content, original_filename)

    monkeypatch.setattr("apps.ingestion.service.store_attachment", fail_second)
    with pytest.raises(OSError, match="second write failed"):
        ingest_file(mailbox, source)
    assert Message.objects.count() == 0
    assert not any(settings.ATTACHMENT_STORAGE_ROOT.rglob("*.*"))


@pytest.mark.django_db
def test_oversized_integrity_race_returns_duplicate(mailbox, settings, fixtures_dir, monkeypatch):
    settings.MAX_MESSAGE_SIZE_MB = 0
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    source = maildir / "new" / "oversized-race"
    source.write_bytes((fixtures_dir / "oversized_simulation.eml").read_bytes())

    monkeypatch.setattr(
        "apps.ingestion.service.Message.objects.create",
        lambda **_kwargs: (_ for _ in ()).throw(IntegrityError("simulated race")),
    )
    assert ingest_file(mailbox, source) == "duplicate"
