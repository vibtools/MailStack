from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from email import policy
from email.header import decode_header, make_header
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

import bleach
from django.utils import timezone

SAFE_TAGS = {
    "p",
    "br",
    "div",
    "span",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "blockquote",
    "pre",
    "code",
    "ul",
    "ol",
    "li",
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "th",
    "td",
    "hr",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a",
    "img",
}
SAFE_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "*": ["class"],
}
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]+")


@dataclass(slots=True)
class ParsedAttachment:
    original_filename: str
    content: bytes
    declared_mime_type: str
    is_inline: bool
    content_id: str


@dataclass(slots=True)
class ParsedMessage:
    message_id_header: str = ""
    sender_name: str = ""
    sender_address: str = ""
    recipient_addresses: list[str] = field(default_factory=list)
    cc_addresses: list[str] = field(default_factory=list)
    subject: str = "(No subject)"
    received_at: datetime | None = None
    text_body: str = ""
    sanitized_html_body: str = ""
    attachments: list[ParsedAttachment] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_header_value(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    try:
        return str(make_header(decode_header(str(value)))).strip() or fallback
    except (LookupError, UnicodeError, ValueError, TypeError):
        return str(value).strip() or fallback


def safe_filename(value: str | None) -> str:
    raw = decode_header_value(value, "attachment.bin").replace("\\", "/")
    name = raw.rsplit("/", 1)[-1]
    name = unicodedata.normalize("NFC", CONTROL_RE.sub("", name)).strip().strip(".")
    allowed_punctuation = frozenset(".()_- +@")
    name = "".join(
        character
        if character in allowed_punctuation
        or character.isalnum()
        or unicodedata.category(character).startswith(("L", "N", "M"))
        else "_"
        for character in name
    )
    if not name:
        name = "attachment.bin"
    return name[:180]


def _safe_attribute(tag: str, name: str, value: str) -> bool:
    lowered = name.lower()
    if lowered.startswith("on") or lowered == "style":
        return False
    if tag == "img" and lowered == "src":
        return value.lower().startswith(
            (
                "data:image/png;base64,",
                "data:image/jpeg;base64,",
                "data:image/gif;base64,",
                "data:image/webp;base64,",
            )
        )
    if tag == "a" and lowered == "href":
        parsed = urlparse(value)
        return parsed.scheme.lower() in {"", "http", "https", "mailto"}
    return True


def sanitize_html(value: str) -> str:
    cleaner = bleach.Cleaner(
        tags=SAFE_TAGS,
        attributes=_safe_attribute,
        protocols={"http", "https", "mailto", "data"},
        strip=True,
        strip_comments=True,
    )
    cleaned = cleaner.clean(value or "")
    return bleach.linkifier.Linker(
        callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank],
        parse_email=False,
    ).linkify(cleaned)


def _decode_part(part) -> str:
    try:
        return part.get_content()
    except (LookupError, UnicodeDecodeError, AttributeError):
        payload = part.get_payload(decode=True) or b""
        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except LookupError:
            return payload.decode("utf-8", errors="replace")


def _parse_date(value: Any, warnings: list[str]) -> datetime | None:
    if not value:
        warnings.append("Missing Date header")
        return None
    try:
        parsed = parsedate_to_datetime(str(value))
        if parsed is None:
            raise ValueError("Date parser returned no value")
        if parsed.tzinfo is None:
            parsed = timezone.make_aware(parsed, timezone.get_default_timezone())
        return parsed
    except (TypeError, ValueError, OverflowError):
        warnings.append("Invalid Date header")
        return None


def parse_message(raw: bytes) -> ParsedMessage:
    result = ParsedMessage()
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw)
    except Exception as exc:
        result.warnings.append(f"MIME parser error: {type(exc).__name__}")
        result.text_body = raw.decode("utf-8", errors="replace")[:100_000]
        return result

    result.message_id_header = decode_header_value(message.get("Message-ID"), "")[:998]
    result.subject = decode_header_value(message.get("Subject"), "(No subject)")[:998]
    sender_pairs = getaddresses(message.get_all("From", []))
    if sender_pairs:
        result.sender_name = decode_header_value(sender_pairs[0][0], "")[:500]
        result.sender_address = sender_pairs[0][1].strip().lower()[:320]
    else:
        result.warnings.append("Missing sender")
    result.recipient_addresses = [
        address.lower() for _name, address in getaddresses(message.get_all("To", [])) if address
    ]
    result.cc_addresses = [
        address.lower() for _name, address in getaddresses(message.get_all("Cc", [])) if address
    ]
    result.received_at = _parse_date(message.get("Date"), result.warnings)

    text_parts: list[str] = []
    html_parts: list[str] = []
    parts = message.walk() if message.is_multipart() else [message]
    for part in parts:
        if part.is_multipart():
            continue
        disposition = (part.get_content_disposition() or "").lower()
        filename = part.get_filename()
        content_type = part.get_content_type().lower()
        is_attachment = disposition == "attachment" or bool(filename)
        if is_attachment or disposition == "inline" and content_type not in {"text/plain", "text/html"}:
            try:
                content = part.get_payload(decode=True) or b""
            except Exception as exc:
                result.warnings.append(f"Attachment decode error: {type(exc).__name__}")
                continue
            result.attachments.append(
                ParsedAttachment(
                    original_filename=decode_header_value(filename, "attachment.bin"),
                    content=content,
                    declared_mime_type=content_type,
                    is_inline=disposition == "inline",
                    content_id=(part.get("Content-ID") or "").strip("<>")[:998],
                )
            )
        elif content_type == "text/plain":
            text_parts.append(_decode_part(part))
        elif content_type == "text/html":
            html_parts.append(_decode_part(part))

    result.text_body = "\n\n".join(text_parts).strip()
    raw_html = "\n".join(html_parts)
    result.sanitized_html_body = sanitize_html(raw_html) if raw_html else ""
    if not result.text_body and not result.sanitized_html_body:
        result.warnings.append("Empty message body")
    return result
