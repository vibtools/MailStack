from __future__ import annotations

import mimetypes
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError

from apps.mailboxes.validators import confined_path

from .parser import safe_filename, sha256_bytes


class AttachmentTooLarge(ValueError):
    """Raised when an attachment exceeds the configured extraction limit."""


def store_attachment(content: bytes, original_filename: str) -> dict[str, object]:
    max_bytes = settings.MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise AttachmentTooLarge(f"Attachment exceeds {settings.MAX_ATTACHMENT_SIZE_MB} MB")
    safe_name = safe_filename(original_filename)
    stored_name = f"{uuid.uuid4().hex}.bin"
    shard = stored_name[:2]
    relative = f"{shard}/{stored_name}"
    path = confined_path(settings.ATTACHMENT_STORAGE_ROOT, shard, stored_name)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    detected, _encoding = mimetypes.guess_type(safe_name, strict=False)
    return {
        "safe_filename": safe_name,
        "stored_filename": stored_name,
        "storage_relative_path": relative,
        "detected_mime_type": detected or "application/octet-stream",
        "size_bytes": len(content),
        "sha256": sha256_bytes(content),
        "path": path,
    }


def delete_stored(relative: str) -> None:
    try:
        path = confined_path(settings.ATTACHMENT_STORAGE_ROOT, relative)
        path.unlink(missing_ok=True)
    except (OSError, ValidationError):
        return
