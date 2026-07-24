from __future__ import annotations

import re
from pathlib import Path

from django.core.exceptions import ValidationError

LOCAL_PART_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?$")
RESERVED_LOCAL_PARTS = {
    "root",
    "admin",
    "administrator",
    "webmaster",
    "hostmaster",
    "mailer-daemon",
    "noreply",
    "no-reply",
    "security",
    "system",
    "support-system",
    "postmaster",
    "abuse",
}


def normalize_local_part(value: str) -> str:
    return (value or "").strip().lower()


def validate_local_part(value: str, *, allow_reserved: bool = False) -> str:
    normalized = normalize_local_part(value)
    if not normalized:
        raise ValidationError("Mailbox local part is required.")
    if len(normalized) > 64:
        raise ValidationError("Mailbox local part must not exceed 64 characters.")
    if ".." in normalized:
        raise ValidationError("Consecutive dots are not allowed.")
    if any(char.isspace() for char in normalized) or "/" in normalized or "\\" in normalized:
        raise ValidationError("Whitespace and path separators are not allowed.")
    if not LOCAL_PART_PATTERN.fullmatch(normalized):
        raise ValidationError(
            "Use lowercase letters, numbers, dot, underscore, or hyphen; "
            "begin and end with a letter or number."
        )
    if not allow_reserved and normalized in RESERVED_LOCAL_PARTS:
        raise ValidationError("This mailbox local part is reserved.")
    return normalized


def confined_path(root: Path, *parts: str) -> Path:
    root_resolved = root.resolve()
    unresolved = root_resolved.joinpath(*parts)
    try:
        relative = unresolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValidationError("Resolved path is outside the configured mail root.") from exc
    current = root_resolved
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ValidationError("Symbolic links are not allowed in confined storage paths.")
    candidate = unresolved.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValidationError("Resolved path is outside the configured mail root.") from exc
    return candidate
