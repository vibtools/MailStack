from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit.services import record_audit
from apps.core.models import ServiceHeartbeat
from apps.mailboxes.models import Mailbox
from apps.mailboxes.services import mailbox_paths
from apps.mailboxes.validators import confined_path
from apps.messages.models import Attachment, Message
from apps.messages.services import recalculate_mailbox_counters

from .parser import parse_message, sha256_bytes
from .storage import AttachmentTooLarge, delete_stored, store_attachment

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionResult:
    scanned: int = 0
    created: int = 0
    duplicates: int = 0
    errors: int = 0
    oversized: int = 0


def source_key(mailbox: Mailbox, source_path: Path) -> str:
    _root, maildir, _relative = mailbox_paths(mailbox.local_part, allow_reserved=True)
    resolved = source_path.resolve()
    try:
        relative = resolved.relative_to(maildir.resolve())
    except ValueError as exc:
        raise ValueError("Source file is outside mailbox Maildir") from exc
    if not relative.parts or relative.parts[0] not in {"new", "cur"}:
        raise ValueError("Source file is not in Maildir/new or Maildir/cur")
    return relative.as_posix()


def update_mailbox_counters(mailbox: Mailbox) -> None:
    with transaction.atomic():
        recalculate_mailbox_counters(mailbox)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ingest_file(mailbox: Mailbox, path: Path, *, dry_run: bool = False) -> str:
    key = source_key(mailbox, path)
    if Message.objects.filter(mailbox=mailbox, source_file_key=key).exists():
        return "duplicate"
    stat = path.stat()
    source_received_at = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
    max_bytes = settings.MAX_MESSAGE_SIZE_MB * 1024 * 1024
    if stat.st_size > max_bytes:
        digest = _sha256_file(path)
        if not dry_run:
            try:
                Message.objects.create(
                    mailbox=mailbox,
                    source_file_key=key,
                    source_sha256=digest,
                    subject="(Oversized message not indexed)",
                    received_at=source_received_at,
                    parsed_at=timezone.now(),
                    size_bytes=stat.st_size,
                    parse_status=Message.ParseStatus.OVERSIZED,
                    parse_warning=f"Message exceeds {settings.MAX_MESSAGE_SIZE_MB} MB",
                )
            except IntegrityError:
                return "duplicate"
            update_mailbox_counters(mailbox)
        logger.warning(
            "Oversized message rejected",
            extra={"event": "oversized_message", "mailbox": mailbox.email_address, "source_file_key": key},
        )
        return "oversized"
    raw = path.read_bytes()
    digest = sha256_bytes(raw)
    parsed = parse_message(raw)
    if dry_run:
        return "created"
    stored_paths: list[str] = []
    try:
        with transaction.atomic():
            message = Message.objects.create(
                mailbox=mailbox,
                source_file_key=key,
                source_sha256=digest,
                message_id_header=parsed.message_id_header,
                sender_name=parsed.sender_name,
                sender_address=parsed.sender_address,
                recipient_addresses=parsed.recipient_addresses,
                cc_addresses=parsed.cc_addresses,
                subject=parsed.subject,
                received_at=parsed.received_at or source_received_at,
                parsed_at=timezone.now(),
                text_body=parsed.text_body,
                sanitized_html_body=parsed.sanitized_html_body,
                size_bytes=len(raw),
                has_attachments=bool(parsed.attachments),
                parse_status=Message.ParseStatus.WARNING if parsed.warnings else Message.ParseStatus.OK,
                parse_warning="; ".join(parsed.warnings)[:4000],
            )
            stored_attachment_count = 0
            for parsed_attachment in parsed.attachments:
                try:
                    stored = store_attachment(parsed_attachment.content, parsed_attachment.original_filename)
                except AttachmentTooLarge as exc:
                    message.parse_status = Message.ParseStatus.WARNING
                    warning = f"Attachment skipped: {exc}"
                    message.parse_warning = "; ".join(filter(None, [message.parse_warning, warning]))[:4000]
                    message.save(update_fields=["parse_status", "parse_warning", "updated_at"])
                    continue
                stored_paths.append(str(stored["storage_relative_path"]))
                Attachment.objects.create(
                    message=message,
                    original_filename=parsed_attachment.original_filename[:1000],
                    safe_filename=str(stored["safe_filename"]),
                    stored_filename=str(stored["stored_filename"]),
                    declared_mime_type=parsed_attachment.declared_mime_type[:255],
                    detected_mime_type=str(stored["detected_mime_type"]),
                    size_bytes=int(stored["size_bytes"]),
                    sha256=str(stored["sha256"]),
                    storage_relative_path=str(stored["storage_relative_path"]),
                    is_inline=parsed_attachment.is_inline,
                    content_id=parsed_attachment.content_id,
                )
                stored_attachment_count += 1
            if message.has_attachments != bool(stored_attachment_count):
                message.has_attachments = bool(stored_attachment_count)
                message.save(update_fields=["has_attachments", "updated_at"])
        update_mailbox_counters(mailbox)
        logger.info(
            "Message ingested",
            extra={
                "event": "message_ingested",
                "mailbox": mailbox.email_address,
                "source_file_key": key,
                "message_uuid": str(message.uuid),
            },
        )
        return "created"
    except IntegrityError:
        for relative in stored_paths:
            delete_stored(relative)
        return "duplicate"
    except Exception as exc:
        for relative in stored_paths:
            delete_stored(relative)
        record_audit(
            "ingestion_error",
            target_type="mailbox",
            target_identifier=mailbox.email_address,
            details={"source_file_key": key, "error_type": type(exc).__name__},
        )
        logger.exception(
            "Message ingestion failed",
            extra={"event": "ingestion_error", "mailbox": mailbox.email_address, "source_file_key": key},
        )
        raise


def iter_maildir_files(mailbox: Mailbox):
    _root, maildir, _relative = mailbox_paths(mailbox.local_part, allow_reserved=True)
    for folder_name in ("new", "cur"):
        folder = confined_path(
            settings.MAIL_STORAGE_ROOT, settings.MAIL_DOMAIN, mailbox.local_part, "Maildir", folder_name
        )
        if not folder.is_dir():
            continue
        with os.scandir(folder) as entries:
            for entry in entries:
                if entry.is_file(follow_symlinks=False):
                    yield Path(entry.path)


def ingest_all(
    *,
    mailbox_local_part: str | None = None,
    dry_run: bool = False,
    rebuild_missing: bool = False,
) -> IngestionResult:
    result = IngestionResult()
    query = Mailbox.objects.filter(deleted_at__isnull=True)
    if mailbox_local_part:
        query = query.filter(local_part__iexact=mailbox_local_part)
    ServiceHeartbeat.objects.update_or_create(
        service_name="maildir_ingestion",
        defaults={
            "status": "running",
            "last_seen_at": timezone.now(),
            "details": {"rebuild_missing": rebuild_missing, "dry_run": dry_run},
        },
    )
    for mailbox in query.iterator():
        for path in iter_maildir_files(mailbox):
            result.scanned += 1
            try:
                outcome = ingest_file(mailbox, path, dry_run=dry_run)
            except Exception:
                result.errors += 1
                continue
            if outcome == "created":
                result.created += 1
            elif outcome == "duplicate":
                result.duplicates += 1
            elif outcome == "oversized":
                result.oversized += 1
    ServiceHeartbeat.objects.update_or_create(
        service_name="maildir_ingestion",
        defaults={
            "status": "healthy" if result.errors == 0 else "degraded",
            "last_seen_at": timezone.now(),
            "details": {**asdict(result), "rebuild_missing": rebuild_missing, "dry_run": dry_run},
        },
    )
    return result
