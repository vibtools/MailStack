from __future__ import annotations

from unittest.mock import patch

import pytest
from django.db import OperationalError

from apps.ingestion.service import ingest_all, ingest_file
from apps.mailboxes.services import mailbox_paths, provision_mailbox
from apps.messages.models import Message


@pytest.mark.django_db
def test_worker_restart_reprocess_is_duplicate(mailbox, fixtures_dir):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    source = maildir / "new" / "restart"
    source.write_bytes((fixtures_dir / "plain_text.eml").read_bytes())
    first = ingest_all()
    second = ingest_all()
    assert first.created == 1
    assert second.duplicates == 1
    assert Message.objects.count() == 1


@pytest.mark.django_db
def test_malformed_then_valid_message_continues(mailbox, fixtures_dir):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    (maildir / "new" / "a-malformed").write_bytes((fixtures_dir / "malformed_mime.eml").read_bytes())
    (maildir / "new" / "b-valid").write_bytes((fixtures_dir / "plain_text.eml").read_bytes())
    result = ingest_all()
    assert result.scanned == 2
    assert result.created == 2
    assert Message.objects.count() == 2


@pytest.mark.django_db
def test_database_failure_is_recorded_and_next_file_continues(mailbox, fixtures_dir, monkeypatch):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    first = maildir / "new" / "first"
    second = maildir / "new" / "second"
    first.write_bytes((fixtures_dir / "plain_text.eml").read_bytes())
    second.write_bytes((fixtures_dir / "html.eml").read_bytes())
    real_create = Message.objects.create
    calls = {"count": 0}

    def flaky_create(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OperationalError("temporary database error")
        return real_create(*args, **kwargs)

    monkeypatch.setattr(Message.objects, "create", flaky_create)
    result = ingest_all()
    assert result.errors == 1
    assert result.created == 1


@pytest.mark.django_db
def test_missing_source_file_raises_without_record(mailbox):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    with pytest.raises(FileNotFoundError):
        ingest_file(mailbox, maildir / "new" / "missing")
    assert Message.objects.count() == 0


@pytest.mark.django_db
def test_maildir_created_after_database_record_is_discovered(settings, fixtures_dir):
    mailbox = provision_mailbox("late")
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    for child in (maildir / "new", maildir / "cur", maildir / "tmp"):
        child.rmdir()
    maildir.rmdir()
    assert (
        list(
            __import__("apps.ingestion.service", fromlist=["iter_maildir_files"]).iter_maildir_files(mailbox)
        )
        == []
    )
    (maildir / "new").mkdir(parents=True)
    (maildir / "cur").mkdir()
    (maildir / "tmp").mkdir()
    (maildir / "new" / "late-delivery").write_bytes((fixtures_dir / "plain_text.eml").read_bytes())
    result = ingest_all(mailbox_local_part="late")
    assert result.created == 1


@pytest.mark.django_db
def test_permission_failure_does_not_create_active_row(settings):
    with patch("pathlib.Path.mkdir", side_effect=PermissionError("denied")), pytest.raises(Exception):
        provision_mailbox("denied")
    assert (
        not __import__("apps.mailboxes.models", fromlist=["Mailbox"])
        .Mailbox.objects.filter(local_part="denied")
        .exists()
    )


@pytest.mark.django_db
def test_counter_rebuild_consistency(mailbox, message):
    for index in range(3):
        Message.objects.create(
            mailbox=mailbox,
            source_file_key=f"cur/{index}",
            source_sha256=f"{index + 1:064x}",
            subject=f"Extra {index}",
            parsed_at=message.parsed_at,
            is_read=index == 0,
        )
    from apps.ingestion.service import update_mailbox_counters

    update_mailbox_counters(mailbox)
    mailbox.refresh_from_db()
    assert mailbox.total_messages == 4
    assert mailbox.unread_messages == 3
