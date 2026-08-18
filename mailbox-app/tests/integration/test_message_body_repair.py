from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.ingestion.service import ingest_file
from apps.mailboxes.services import mailbox_paths
from apps.messages.models import Message


def _ingest_fixture(mailbox, fixtures_dir: Path, name: str, source_name: str) -> Message:
    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    source = maildir / "new" / source_name
    source.write_bytes((fixtures_dir / name).read_bytes())
    assert ingest_file(mailbox, source) == "created"
    return Message.objects.get(mailbox=mailbox, source_file_key=f"new/{source_name}")


@pytest.mark.django_db
def test_repair_message_bodies_requires_explicit_confirmation(mailbox):
    with pytest.raises(CommandError, match="--confirm-repair"):
        call_command("repair_message_bodies", mailbox=mailbox.local_part)


@pytest.mark.django_db
def test_repair_message_bodies_dry_run_then_mutation_preserves_state(mailbox, fixtures_dir):
    message = _ingest_fixture(mailbox, fixtures_dir, "html_style_heavy.eml", "repair-html")
    message.sanitized_html_body = "#outlook a { padding: 0; } broken body"
    message.is_read = True
    message.deleted_at = timezone.now()
    message.save(update_fields=["sanitized_html_body", "is_read", "deleted_at", "updated_at"])

    original = {
        "pk": message.pk,
        "uuid": message.uuid,
        "source_file_key": message.source_file_key,
        "source_sha256": message.source_sha256,
        "mailbox_id": message.mailbox_id,
        "is_read": message.is_read,
        "deleted_at": message.deleted_at,
    }

    dry_output = StringIO()
    call_command(
        "repair_message_bodies",
        mailbox=mailbox.local_part,
        dry_run=True,
        stdout=dry_output,
    )
    assert "would_update=1" in dry_output.getvalue()
    message.refresh_from_db()
    assert message.sanitized_html_body.startswith("#outlook")

    output = StringIO()
    call_command(
        "repair_message_bodies",
        mailbox=mailbox.local_part,
        confirm_repair=True,
        stdout=output,
    )
    assert "updated=1" in output.getvalue()

    message.refresh_from_db()
    assert "Welcome to Harpoon!" in message.sanitized_html_body
    assert "#outlook" not in message.sanitized_html_body
    assert message.pk == original["pk"]
    assert message.uuid == original["uuid"]
    assert message.source_file_key == original["source_file_key"]
    assert message.source_sha256 == original["source_sha256"]
    assert message.mailbox_id == original["mailbox_id"]
    assert message.is_read == original["is_read"]
    assert message.deleted_at == original["deleted_at"]

    second_output = StringIO()
    call_command(
        "repair_message_bodies",
        mailbox=mailbox.local_part,
        confirm_repair=True,
        stdout=second_output,
    )
    assert "updated=0" in second_output.getvalue()
    assert "unchanged=1" in second_output.getvalue()


@pytest.mark.django_db
def test_repair_message_bodies_preserves_attachment_identity(mailbox, fixtures_dir):
    message = _ingest_fixture(mailbox, fixtures_dir, "one_attachment.eml", "repair-attachment")
    attachment = message.attachments.get()
    attachment_identity = (
        attachment.pk,
        attachment.uuid,
        attachment.sha256,
        attachment.storage_relative_path,
    )
    message.text_body = "stale"
    message.save(update_fields=["text_body", "updated_at"])

    call_command(
        "repair_message_bodies",
        message=str(message.uuid),
        confirm_repair=True,
        stdout=StringIO(),
    )

    message.refresh_from_db()
    attachment.refresh_from_db()
    assert message.text_body.strip() == "One attachment."
    assert message.attachments.count() == 1
    assert (
        attachment.pk,
        attachment.uuid,
        attachment.sha256,
        attachment.storage_relative_path,
    ) == attachment_identity


@pytest.mark.django_db
def test_repair_message_bodies_reports_missing_and_mismatched_sources(mailbox, fixtures_dir):
    missing = _ingest_fixture(mailbox, fixtures_dir, "html.eml", "repair-missing")
    mismatch = _ingest_fixture(mailbox, fixtures_dir, "plain_text.eml", "repair-mismatch")

    _root, maildir, _relative = mailbox_paths(mailbox.local_part)
    (maildir / missing.source_file_key).unlink()
    (maildir / mismatch.source_file_key).write_bytes(b"changed source")

    output = StringIO()
    call_command(
        "repair_message_bodies",
        mailbox=mailbox.local_part,
        dry_run=True,
        stdout=output,
    )
    summary = output.getvalue()
    assert "missing=1" in summary
    assert "mismatch=1" in summary
    assert "updated=0" in summary
