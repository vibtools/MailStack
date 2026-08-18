from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError

from apps.ingestion.parser import (
    decode_header_value,
    parse_message,
    safe_filename,
    sanitize_html,
    sha256_bytes,
)
from apps.ingestion.storage import AttachmentTooLarge, delete_stored, store_attachment


def test_sha256_bytes():
    assert sha256_bytes(b"abc") == hashlib.sha256(b"abc").hexdigest()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("../../etc/passwd", "passwd"),
        (r"C:\\Windows\\evil.exe", "evil.exe"),
        ("...", "attachment.bin"),
        ("line\nfeed.txt", "linefeed.txt"),
        ("প্রতিবেদন.txt", "প্রতিবেদন.txt"),
    ],
)
def test_safe_filename(raw, expected):
    assert safe_filename(raw) == expected


def test_decode_header_value_handles_none_and_encoded():
    assert decode_header_value(None, "fallback") == "fallback"
    assert "বাংলা" in decode_header_value("=?utf-8?b?4Kas4Ka+4KaC4Kay4Ka+?=")


def test_sanitize_html_links_urls_but_never_linkifies_email_addresses():
    cleaned = sanitize_html("<p>user@example.com https://example.com/path</p>")
    assert "mailto:" not in cleaned
    assert 'href="https://example.com/path"' in cleaned


def test_sanitize_html_removes_active_and_remote_content():
    value = """
    <script>alert(1)</script><iframe src='https://evil.test'></iframe>
    <form><input value='x'><button>go</button></form>
    <p onclick='bad()' style='background:url(https://tracker.test)'>Text</p>
    <a href='javascript:alert(1)'>bad</a>
    <img src='https://tracker.test/pixel.png' onerror='bad()'>
    <img src='data:image/png;base64,AA==' alt='ok'>
    """
    cleaned = sanitize_html(value)
    lowered = cleaned.lower()
    assert "<script" not in lowered
    assert "<iframe" not in lowered
    assert "<form" not in lowered
    assert "onclick" not in lowered
    assert "javascript:" not in lowered
    assert "tracker.test" not in lowered
    assert "alert(1)" not in lowered
    assert "<img" in lowered
    assert "data:image/png;base64,aa==" in lowered
    assert "Text" in cleaned


def test_sanitize_html_drops_style_block_text_and_remote_image_nodes():
    cleaned = sanitize_html(
        "<html><head><style>#outlook a{padding:0}.ReadMsgBody{width:100%}</style></head>"
        "<body><p>Readable email content</p>"
        "<img src='https://tracker.test/pixel.png' alt='intercom'></body></html>"
    )
    lowered = cleaned.lower()
    assert "#outlook" not in lowered
    assert ".readmsgbody" not in lowered
    assert "tracker.test" not in lowered
    assert "intercom" not in lowered
    assert "<img" not in lowered
    assert "Readable email content" in cleaned


@pytest.mark.parametrize(
    "fixture_name",
    [
        "plain_text.eml",
        "html.eml",
        "html_style_heavy.eml",
        "multipart_alternative.eml",
        "nested_multipart.eml",
        "utf8_subject.eml",
        "utf8_sender.eml",
        "missing_subject.eml",
        "missing_date.eml",
        "invalid_date.eml",
        "missing_message_id.eml",
        "empty_body.eml",
        "malformed_mime.eml",
    ],
)
def test_parse_message_fixture_matrix(fixtures_dir: Path, fixture_name: str):
    parsed = parse_message((fixtures_dir / fixture_name).read_bytes())
    assert isinstance(parsed.subject, str)
    assert isinstance(parsed.text_body, str)
    assert isinstance(parsed.sanitized_html_body, str)
    assert isinstance(parsed.warnings, list)


def test_parse_message_style_heavy_html_is_readable_without_css_leak(fixtures_dir: Path):
    parsed = parse_message((fixtures_dir / "html_style_heavy.eml").read_bytes())
    lowered = parsed.sanitized_html_body.lower()
    assert "Welcome to Harpoon!" in parsed.sanitized_html_body
    assert "This content must stay readable." in parsed.sanitized_html_body
    assert "#outlook" not in lowered
    assert ".readmsgbody" not in lowered
    assert "alert(1)" not in lowered
    assert "tracker.example.test" not in lowered
    assert "intercom" not in lowered


def test_parse_message_extracts_headers_bodies_and_attachments(fixtures_dir: Path):
    parsed = parse_message((fixtures_dir / "one_attachment.eml").read_bytes())
    assert parsed.sender_address == "sender@example.test"
    assert parsed.recipient_addresses == ["mailbox1@example.com"]
    assert parsed.subject == "One attachment"
    assert parsed.text_body.strip() == "One attachment."
    assert len(parsed.attachments) == 1
    assert parsed.attachments[0].original_filename == "alpha.txt"
    assert parsed.attachments[0].content == b"alpha"


def test_parse_message_security_fixtures(fixtures_dir: Path):
    for name in [
        "html_script.eml",
        "html_iframe.eml",
        "html_event_handler.eml",
        "html_javascript_url.eml",
        "html_remote_image.eml",
    ]:
        parsed = parse_message((fixtures_dir / name).read_bytes())
        lowered = parsed.sanitized_html_body.lower()
        assert "<script" not in lowered
        assert "<iframe" not in lowered
        assert "onerror" not in lowered
        assert "javascript:" not in lowered
        assert "tracker.test" not in lowered


def test_store_and_delete_attachment(settings):
    stored = store_attachment(b"content", "../report.txt")
    path = Path(stored["path"])
    assert path.is_file()
    assert path.read_bytes() == b"content"
    assert stored["safe_filename"] == "report.txt"
    assert stored["sha256"] == hashlib.sha256(b"content").hexdigest()
    assert path.is_relative_to(settings.ATTACHMENT_STORAGE_ROOT)
    delete_stored(str(stored["storage_relative_path"]))
    assert not path.exists()


def test_store_attachment_size_limit(settings):
    settings.MAX_ATTACHMENT_SIZE_MB = 0
    with pytest.raises(AttachmentTooLarge):
        store_attachment(b"x", "x.bin")


def test_delete_stored_ignores_escaped_path(settings):
    outside = settings.ATTACHMENT_STORAGE_ROOT.parent / "outside.bin"
    outside.write_bytes(b"safe")
    delete_stored("../outside.bin")
    assert outside.read_bytes() == b"safe"


def test_confined_storage_rejects_absolute_escape(settings):
    with pytest.raises(ValidationError):
        from apps.mailboxes.validators import confined_path

        confined_path(settings.ATTACHMENT_STORAGE_ROOT, "/etc/passwd")


def test_decode_header_value_falls_back_when_decoder_raises(monkeypatch):
    def fail_decode(_value):
        raise LookupError("unknown codec")

    monkeypatch.setattr("apps.ingestion.parser.decode_header", fail_decode)
    assert decode_header_value("raw value", "fallback") == "raw value"


def test_decode_part_uses_charset_and_utf8_fallback():
    from apps.ingestion.parser import _decode_part

    class FallbackPart:
        def get_content(self):
            raise LookupError("decode failed")

        def get_payload(self, *, decode=False):
            assert decode is True
            return b"\xfftext"

        def get_content_charset(self):
            return "unknown-charset"

    assert _decode_part(FallbackPart()).endswith("text")


def test_parse_date_handles_naive_and_parser_none(monkeypatch):
    from apps.ingestion.parser import _parse_date

    warnings: list[str] = []
    parsed = _parse_date("Fri, 26 Jun 2026 10:00:00", warnings)
    assert parsed is not None
    assert parsed.tzinfo is not None

    monkeypatch.setattr("apps.ingestion.parser.parsedate_to_datetime", lambda _value: None)
    assert _parse_date("not-empty", warnings) is None
    assert "Invalid Date header" in warnings


def test_parse_message_recovers_from_parser_exception(monkeypatch):
    class BrokenParser:
        def __init__(self, **kwargs):
            self.options = kwargs

        def parsebytes(self, _raw):
            raise ValueError("malformed")

    monkeypatch.setattr("apps.ingestion.parser.BytesParser", BrokenParser)
    parsed = parse_message(b"raw fallback")
    assert parsed.text_body == "raw fallback"
    assert parsed.warnings == ["MIME parser error: ValueError"]


def test_parse_message_warns_when_sender_is_missing():
    parsed = parse_message(b"To: mailbox1@example.com\nSubject: Missing sender\n\nBody")
    assert "Missing sender" in parsed.warnings


def test_parse_message_continues_after_attachment_decode_error(monkeypatch):
    class AttachmentPart:
        def is_multipart(self):
            return False

        def get_content_disposition(self):
            return "attachment"

        def get_filename(self):
            return "broken.bin"

        def get_content_type(self):
            return "application/octet-stream"

        def get_payload(self, *, decode=False):
            assert decode is True
            raise ValueError("cannot decode")

    class FakeMessage:
        def get(self, _name, default=None):
            return default

        def get_all(self, _name, default=None):
            return default or []

        def is_multipart(self):
            return True

        def walk(self):
            return [self, AttachmentPart()]

    class FakeParser:
        def __init__(self, **kwargs):
            self.options = kwargs

        def parsebytes(self, _raw):
            return FakeMessage()

    monkeypatch.setattr("apps.ingestion.parser.BytesParser", FakeParser)
    parsed = parse_message(b"ignored")
    assert "Attachment decode error: ValueError" in parsed.warnings
    assert parsed.attachments == []
