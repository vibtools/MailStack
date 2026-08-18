from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.mailboxes.validators import confined_path
from apps.messages.models import Message

from .parser import parse_message, sha256_bytes

logger = logging.getLogger(__name__)


class BodyRepairError(RuntimeError):
    """Base class for non-destructive message-body repair failures."""


class RepairSourceMissing(BodyRepairError):
    """The original Maildir source no longer exists."""


class RepairSourceMismatch(BodyRepairError):
    """The source file no longer matches the indexed source SHA-256."""


class RepairSourceTooLarge(BodyRepairError):
    """The source exceeds the configured message-size limit."""


@dataclass(slots=True, frozen=True)
class BodyRepairResult:
    status: str
    warning_count: int = 0


def source_path_for_message(message: Message) -> Path:
    key = PurePosixPath(message.source_file_key)
    parts = key.parts
    if key.is_absolute() or len(parts) < 2 or parts[0] not in {"new", "cur"}:
        raise BodyRepairError("Unsafe source_file_key")
    if any(part in {"", ".", ".."} for part in parts):
        raise BodyRepairError("Unsafe source_file_key")
    try:
        return confined_path(
            settings.MAIL_STORAGE_ROOT,
            settings.MAIL_DOMAIN,
            message.mailbox.local_part,
            "Maildir",
            *parts,
        )
    except ValidationError as exc:
        raise BodyRepairError("Unsafe Maildir source path") from exc


def repair_message_bodies(message: Message, *, dry_run: bool = False) -> BodyRepairResult:
    source = source_path_for_message(message)
    if not source.is_file():
        raise RepairSourceMissing("Original Maildir source file is missing")

    max_bytes = settings.MAX_MESSAGE_SIZE_MB * 1024 * 1024
    if source.stat().st_size > max_bytes:
        raise RepairSourceTooLarge("Source exceeds configured maximum message size")

    raw = source.read_bytes()
    if sha256_bytes(raw) != message.source_sha256:
        raise RepairSourceMismatch("Maildir source SHA-256 no longer matches indexed source")

    parsed = parse_message(raw)
    changed = (
        parsed.text_body != message.text_body
        or parsed.sanitized_html_body != message.sanitized_html_body
    )
    if not changed:
        return BodyRepairResult(status="unchanged", warning_count=len(parsed.warnings))
    if dry_run:
        return BodyRepairResult(status="would_update", warning_count=len(parsed.warnings))

    with transaction.atomic():
        locked = Message.objects.select_for_update().get(pk=message.pk)
        if locked.source_file_key != message.source_file_key or locked.source_sha256 != message.source_sha256:
            raise RepairSourceMismatch("Indexed source identity changed during repair")
        Message.objects.filter(pk=locked.pk).update(
            text_body=parsed.text_body,
            sanitized_html_body=parsed.sanitized_html_body,
        )

    logger.info(
        "Message bodies repaired",
        extra={
            "event": "message_body_repaired",
            "message_uuid": str(message.uuid),
            "mailbox": message.mailbox.email_address,
        },
    )
    return BodyRepairResult(status="updated", warning_count=len(parsed.warnings))
