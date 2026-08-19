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
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import bleach
import tinycss2
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
    "style",
}
SAFE_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "*": ["class"],
}
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]+")

DROP_CONTENT_TAGS = frozenset({"script", "noscript", "template", "title"})
SAFE_DATA_IMAGE_PREFIXES = (
    "data:image/png;base64,",
    "data:image/jpeg;base64,",
    "data:image/gif;base64,",
    "data:image/webp;base64,",
)

CSS_BLOCK_MAX_INPUT_BYTES = 128 * 1024
CSS_TOTAL_MAX_RETAINED_BYTES = 256 * 1024
CSS_MAX_RETAINED_RULES = 512
CSS_MAX_NESTING_DEPTH = 8
CSS_ALLOWED_PROPERTIES = frozenset(
    {
        "background-color",
        "border",
        "border-bottom",
        "border-bottom-color",
        "border-bottom-style",
        "border-bottom-width",
        "border-collapse",
        "border-color",
        "border-left",
        "border-left-color",
        "border-left-style",
        "border-left-width",
        "border-radius",
        "border-right",
        "border-right-color",
        "border-right-style",
        "border-right-width",
        "border-spacing",
        "border-style",
        "border-top",
        "border-top-color",
        "border-top-style",
        "border-top-width",
        "border-width",
        "box-sizing",
        "clear",
        "color",
        "display",
        "empty-cells",
        "float",
        "font-family",
        "font-size",
        "font-style",
        "font-variant",
        "font-weight",
        "height",
        "letter-spacing",
        "line-height",
        "list-style-position",
        "list-style-type",
        "margin",
        "margin-bottom",
        "margin-left",
        "margin-right",
        "margin-top",
        "max-height",
        "max-width",
        "min-height",
        "min-width",
        "overflow",
        "overflow-wrap",
        "padding",
        "padding-bottom",
        "padding-left",
        "padding-right",
        "padding-top",
        "table-layout",
        "text-align",
        "text-decoration",
        "text-indent",
        "text-transform",
        "vertical-align",
        "white-space",
        "width",
        "word-break",
    }
)
CSS_ALLOWED_FUNCTIONS = frozenset({"calc", "clamp", "hsl", "hsla", "max", "min", "rgb", "rgba"})
CSS_ALLOWED_MEDIA_TYPES = frozenset({"all", "screen"})
CSS_ALLOWED_MEDIA_FEATURES = frozenset({"max-width", "min-width", "orientation", "width"})
CSS_ALLOWED_ORIENTATIONS = frozenset({"landscape", "portrait"})
CSS_ALLOWED_LENGTH_UNITS = frozenset(
    {
        "ch",
        "cm",
        "em",
        "ex",
        "in",
        "mm",
        "pc",
        "pt",
        "px",
        "q",
        "rem",
        "vh",
        "vmax",
        "vmin",
        "vw",
    }
)
CSS_FORBIDDEN_TEXT = (
    "javascript:",
    "vbscript:",
    "expression(",
    "url(",
    "var(",
    "env(",
    "attr(",
    "</style",
)


@dataclass(slots=True)
class _CSSBudget:
    retained_bytes: int = 0
    retained_rules: int = 0

    def reserve(self, fragment: str, *, rules: int = 0) -> bool:
        fragment_bytes = len(fragment.encode("utf-8", errors="ignore"))
        if self.retained_bytes + fragment_bytes > CSS_TOTAL_MAX_RETAINED_BYTES:
            return False
        if self.retained_rules + rules > CSS_MAX_RETAINED_RULES:
            return False
        self.retained_bytes += fragment_bytes
        self.retained_rules += rules
        return True


def _css_input_within_limit(value: str) -> bool:
    return len((value or "").encode("utf-8", errors="ignore")) <= CSS_BLOCK_MAX_INPUT_BYTES


def _css_component_values_safe(tokens, *, depth: int = 0) -> bool:
    if depth > CSS_MAX_NESTING_DEPTH:
        return False
    for token in tokens:
        node_kind = getattr(token, "type", "")
        if node_kind in {"error", "url"}:
            return False
        if node_kind == "at-keyword":
            return False
        if node_kind == "function":
            if getattr(token, "lower_name", "") not in CSS_ALLOWED_FUNCTIONS:
                return False
            if not _css_component_values_safe(getattr(token, "arguments", ()), depth=depth + 1):
                return False
            continue
        nested = getattr(token, "content", None)
        if nested is not None and not _css_component_values_safe(nested, depth=depth + 1):
            return False
    serialized = tinycss2.serialize(tokens).casefold().replace("\\", "")
    return not any(forbidden in serialized for forbidden in CSS_FORBIDDEN_TEXT)


def _sanitize_declaration_tokens(tokens) -> str:
    safe_declarations: list[str] = []
    for token in tokens:
        if getattr(token, "type", "") != "declaration":
            continue
        property_name = getattr(token, "lower_name", "")
        if not property_name or property_name.startswith("--"):
            continue
        if property_name not in CSS_ALLOWED_PROPERTIES:
            continue
        value_tokens = getattr(token, "value", ())
        if not _css_component_values_safe(value_tokens):
            continue
        value = tinycss2.serialize(value_tokens).strip()
        if not value:
            continue
        declaration = f"{property_name}:{value}"
        if getattr(token, "important", False):
            declaration += " !important"
        safe_declarations.append(declaration + ";")
    return "".join(safe_declarations)


def _sanitize_declarations(value: str) -> str:
    if not _css_input_within_limit(value):
        return ""
    tokens = tinycss2.parse_blocks_contents(value or "", skip_comments=True, skip_whitespace=True)
    return _sanitize_declaration_tokens(tokens)


def _media_feature_safe(block) -> bool:
    content = [token for token in getattr(block, "content", ()) if getattr(token, "type", "") != "whitespace"]
    if len(content) < 3:
        return False
    name_token, colon_token, *value_tokens = content
    if getattr(name_token, "type", "") != "ident":
        return False
    feature = getattr(name_token, "lower_value", "")
    if feature not in CSS_ALLOWED_MEDIA_FEATURES:
        return False
    if getattr(colon_token, "type", "") != "literal" or getattr(colon_token, "value", "") != ":":
        return False
    if not value_tokens:
        return False
    if feature == "orientation":
        return len(value_tokens) == 1 and getattr(value_tokens[0], "type", "") == "ident" and getattr(
            value_tokens[0], "lower_value", ""
        ) in CSS_ALLOWED_ORIENTATIONS
    if len(value_tokens) != 1:
        return False
    value_token = value_tokens[0]
    node_kind = getattr(value_token, "type", "")
    if node_kind == "number":
        return float(getattr(value_token, "value", -1)) == 0
    if node_kind != "dimension":
        return False
    if float(getattr(value_token, "value", -1)) < 0:
        return False
    return getattr(value_token, "lower_unit", "") in CSS_ALLOWED_LENGTH_UNITS


def _media_prelude_safe(tokens) -> bool:
    meaningful = [token for token in tokens if getattr(token, "type", "") != "whitespace"]
    if not meaningful:
        return False
    expect_term = True
    saw_term = False
    for token in meaningful:
        node_kind = getattr(token, "type", "")
        if expect_term:
            if node_kind == "ident" and getattr(token, "lower_value", "") in CSS_ALLOWED_MEDIA_TYPES:
                saw_term = True
                expect_term = False
                continue
            if node_kind == "() block" and _media_feature_safe(token):
                saw_term = True
                expect_term = False
                continue
            return False
        if node_kind == "ident" and getattr(token, "lower_value", "") == "and":
            expect_term = True
            continue
        return False
    return saw_term and not expect_term


def _sanitize_rule(rule, *, depth: int = 0) -> tuple[str, int] | None:
    rule_type = getattr(rule, "type", "")
    if rule_type == "qualified-rule":
        selector = tinycss2.serialize(getattr(rule, "prelude", ())).strip()
        if not selector or "</style" in selector.casefold():
            return None
        declarations = tinycss2.parse_blocks_contents(
            getattr(rule, "content", ()), skip_comments=True, skip_whitespace=True
        )
        sanitized = _sanitize_declaration_tokens(declarations)
        if not sanitized:
            return None
        return f"{selector}{{{sanitized}}}", 1
    if rule_type != "at-rule" or getattr(rule, "lower_at_keyword", "") != "media":
        return None
    if depth >= CSS_MAX_NESTING_DEPTH:
        return None
    content = getattr(rule, "content", None)
    if content is None or not _media_prelude_safe(getattr(rule, "prelude", ())):
        return None
    nested_rules = tinycss2.parse_rule_list(content, skip_comments=True, skip_whitespace=True)
    nested_fragments: list[str] = []
    nested_count = 0
    for nested_rule in nested_rules:
        sanitized_nested = _sanitize_rule(nested_rule, depth=depth + 1)
        if sanitized_nested is None:
            continue
        fragment, count = sanitized_nested
        nested_fragments.append(fragment)
        nested_count += count
    if not nested_fragments:
        return None
    media = tinycss2.serialize(getattr(rule, "prelude", ())).strip()
    return f"@media {media}{{{''.join(nested_fragments)}}}", nested_count + 1


class _MailStackCSSSanitizer:
    """Sanitize email presentation CSS without permitting resource loading or active behavior."""

    def __init__(self, budget: _CSSBudget) -> None:
        self.budget = budget

    def sanitize_css(self, style: str) -> str:
        sanitized = _sanitize_declarations(style)
        if not sanitized or not self.budget.reserve(sanitized):
            return ""
        return sanitized

    def sanitize_stylesheet(self, stylesheet: str) -> str:
        if not _css_input_within_limit(stylesheet):
            return ""
        rules = tinycss2.parse_stylesheet(stylesheet or "", skip_comments=True, skip_whitespace=True)
        fragments: list[str] = []
        for rule in rules:
            sanitized_rule = _sanitize_rule(rule)
            if sanitized_rule is None:
                continue
            fragment, count = sanitized_rule
            if not self.budget.reserve(fragment, rules=count):
                break
            fragments.append(fragment)
        return "".join(fragments)


class _SanitizerPreprocessor(HTMLParser):
    """Remove non-display/active blocks and unusable remote images before Bleach."""

    def __init__(self, css_sanitizer: _MailStackCSSSanitizer) -> None:
        super().__init__(convert_charrefs=False)
        self.output: list[str] = []
        self._suppressed_depth = 0
        self._head_depth = 0
        self._style_depth = 0
        self._style_buffer: list[str] = []
        self._css_sanitizer = css_sanitizer

    @staticmethod
    def _safe_image(attrs: list[tuple[str, str | None]]) -> bool:
        source = next((value or "" for name, value in attrs if name.lower() == "src"), "")
        return source.lower().startswith(SAFE_DATA_IMAGE_PREFIXES)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if self._suppressed_depth:
            if lowered in DROP_CONTENT_TAGS:
                self._suppressed_depth += 1
            return
        if self._style_depth:
            return
        if lowered == "head":
            self._head_depth += 1
            return
        if self._head_depth:
            if lowered in DROP_CONTENT_TAGS:
                self._suppressed_depth = 1
                return
            if lowered == "style":
                self._style_depth = 1
                self._style_buffer = []
            return
        if lowered in DROP_CONTENT_TAGS:
            self._suppressed_depth = 1
            return
        if lowered == "style":
            self._style_depth = 1
            self._style_buffer = []
            return
        if lowered == "img" and not self._safe_image(attrs):
            return
        self.output.append(self.get_starttag_text() or f"<{lowered}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if (
            self._suppressed_depth
            or self._style_depth
            or self._head_depth
            or lowered == "head"
            or lowered in DROP_CONTENT_TAGS
            or lowered == "style"
        ):
            return
        if lowered == "img" and not self._safe_image(attrs):
            return
        self.output.append(self.get_starttag_text() or f"<{lowered}/>")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if self._suppressed_depth:
            if lowered in DROP_CONTENT_TAGS:
                self._suppressed_depth -= 1
            return
        if self._style_depth:
            if lowered == "style":
                self._style_depth = 0
                sanitized = self._css_sanitizer.sanitize_stylesheet("".join(self._style_buffer))
                self._style_buffer = []
                if sanitized:
                    self.output.append(f"<style>{sanitized}</style>")
            return
        if self._head_depth:
            if lowered == "head":
                self._head_depth -= 1
            return
        if lowered == "head":
            return
        self.output.append(f"</{lowered}>")

    def handle_data(self, data: str) -> None:
        if self._style_depth:
            self._style_buffer.append(data)
        elif not self._suppressed_depth and not self._head_depth:
            self.output.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._style_depth:
            self._style_buffer.append(f"&{name};")
        elif not self._suppressed_depth and not self._head_depth:
            self.output.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._style_depth:
            self._style_buffer.append(f"&#{name};")
        elif not self._suppressed_depth and not self._head_depth:
            self.output.append(f"&#{name};")


def _prepare_html_for_sanitizer(value: str, css_sanitizer: _MailStackCSSSanitizer) -> str:
    parser = _SanitizerPreprocessor(css_sanitizer)
    parser.feed(value or "")
    parser.close()
    return "".join(parser.output)


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
    if lowered.startswith("on"):
        return False
    if tag == "img" and lowered == "src":
        return value.lower().startswith(SAFE_DATA_IMAGE_PREFIXES)
    if tag == "a" and lowered == "href":
        parsed = urlparse(value)
        return parsed.scheme.lower() in {"", "http", "https", "mailto"}
    return True


def sanitize_html(value: str) -> str:
    css_sanitizer = _MailStackCSSSanitizer(_CSSBudget())
    cleaner = bleach.Cleaner(
        tags=SAFE_TAGS,
        attributes=_safe_attribute,
        protocols={"http", "https", "mailto", "data"},
        strip=True,
        strip_comments=True,
        css_sanitizer=css_sanitizer,
    )
    prepared = _prepare_html_for_sanitizer(value, css_sanitizer)
    cleaned = cleaner.clean(prepared)
    return bleach.linkifier.Linker(
        callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank],
        skip_tags={"style"},
        parse_email=False,
    ).linkify(cleaned).strip()


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
