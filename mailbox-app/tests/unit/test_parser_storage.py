from __future__ import annotations

import hashlib
import re
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


def test_sanitize_html_preserves_safe_style_block_without_visible_css_leak():
    cleaned = sanitize_html(
        "<html><head><style>#outlook a{padding:0}.ReadMsgBody{width:100%}</style></head>"
        "<body><p>Readable email content</p>"
        "<img src='https://tracker.test/pixel.png' alt='intercom'></body></html>"
    )
    lowered = cleaned.lower()
    assert "<style>" in lowered
    assert "#outlook a{padding:0;}" in lowered
    assert ".readmsgbody{width:100%;}" in lowered
    assert "tracker.test" not in lowered
    assert "intercom" not in lowered
    assert "<img" not in lowered
    assert "Readable email content" in cleaned
    visible_markup = re.sub(r"<style>.*?</style>", "", lowered, flags=re.DOTALL)
    assert "#outlook" not in visible_markup
    assert ".readmsgbody" not in visible_markup


def test_sanitize_html_keeps_only_sanitized_style_from_head():
    cleaned = sanitize_html(
        "<html><head>HEAD SECRET"
        "<title>Hidden title</title>"
        "<meta name='description' content='hidden'>"
        "<script>alert('head')</script>"
        "<style>.brand{color:#123456;background-image:url(https://tracker.test/bg.png)}</style>"
        "</head><body><p class='brand'>Visible body</p></body></html>"
    )
    lowered = cleaned.lower()
    assert "head secret" not in lowered
    assert "hidden title" not in lowered
    assert "description" not in lowered
    assert "alert(" not in lowered
    assert "tracker.test" not in lowered
    assert ".brand{color:#123456;}" in lowered
    assert "Visible body" in cleaned


def test_sanitize_html_preserves_safe_inline_css_and_drops_unsafe_declarations():
    cleaned = sanitize_html(
        '<p style="color:red;padding:12px;width:calc(100% - 20px);'
        'background-image:url(https://tracker.test/bg.png);position:fixed">Styled</p>'
    )
    lowered = cleaned.lower()
    assert "color:red;" in lowered
    assert "padding:12px;" in lowered
    assert "width:calc(100% - 20px);" in lowered
    assert "background-image" not in lowered
    assert "tracker.test" not in lowered
    assert "position:fixed" not in lowered


def test_sanitize_html_allows_bounded_media_rules_and_drops_other_at_rules():
    cleaned = sanitize_html(
        "<style>"
        "@import url(https://tracker.test/x.css);"
        "@font-face{font-family:Evil;src:url(https://tracker.test/e.woff2)}"
        "@media screen and (max-width:600px){.responsive{width:100%;display:block}}"
        "@media screen and (prefers-color-scheme:dark){.dark{color:white}}"
        "</style><div class='responsive'>Responsive</div>"
    )
    lowered = cleaned.lower()
    assert "@media screen and (max-width:600px)" in lowered
    assert ".responsive{width:100%;display:block;}" in lowered
    assert "@import" not in lowered
    assert "@font-face" not in lowered
    assert "prefers-color-scheme" not in lowered
    assert "tracker.test" not in lowered


def test_sanitize_html_css_fail_closed_limits_do_not_drop_message_content():
    oversized = "color:red;" * 20_000
    cleaned = sanitize_html(f'<p style="{oversized}">Still readable</p>')
    assert "Still readable" in cleaned
    assert 'style=""' in cleaned or "style" not in cleaned

    oversized_stylesheet = ".safe{color:red;}" * 10_000
    cleaned = sanitize_html(f"<style>{oversized_stylesheet}</style><p>Body survives</p>")
    assert "Body survives" in cleaned
    assert "<style>" not in cleaned.lower()


def test_sanitize_html_css_blocks_data_urls_custom_properties_and_dynamic_functions():
    cleaned = sanitize_html(
        '<p style="color:var(--brand);--brand:red;background-image:url(data:image/png;base64,AAAA);'
        'width:env(safe-area-inset-left);font-size:attr(data-size px);padding:8px">Safe</p>'
    ).lower()
    assert "padding:8px;" in cleaned
    assert "--brand" not in cleaned
    assert "var(" not in cleaned
    assert "env(" not in cleaned
    assert "attr(" not in cleaned
    assert "url(" not in cleaned
    assert "data:image" not in cleaned


@pytest.mark.parametrize(
    "fixture_name",
    [
        "plain_text.eml",
        "html.eml",
        "html_style_heavy.eml",
        "html_style_safe.eml",
        "html_style_unsafe.eml",
        "html_inline_style.eml",
        "html_media_style.eml",
        "html_table_layout.eml",
        "html_malformed_css.eml",
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


def test_parse_message_style_heavy_html_is_readable_with_sanitized_css(fixtures_dir: Path):
    parsed = parse_message((fixtures_dir / "html_style_heavy.eml").read_bytes())
    lowered = parsed.sanitized_html_body.lower()
    assert "Welcome to Harpoon!" in parsed.sanitized_html_body
    assert "This content must stay readable." in parsed.sanitized_html_body
    assert "#outlook a{padding:0;}" in lowered
    assert ".readmsgbody{width:100%;}" in lowered
    assert "body{width:100% !important;}" in lowered
    assert "alert(1)" not in lowered
    assert "tracker.example.test" not in lowered
    assert "intercom" not in lowered
    visible_markup = re.sub(r"<style>.*?</style>", "", lowered, flags=re.DOTALL)
    assert "#outlook" not in visible_markup
    assert ".readmsgbody" not in visible_markup


def test_parse_message_css_fixture_contract(fixtures_dir: Path):
    safe = parse_message((fixtures_dir / "html_style_safe.eml").read_bytes()).sanitized_html_body.lower()
    unsafe = parse_message((fixtures_dir / "html_style_unsafe.eml").read_bytes()).sanitized_html_body.lower()
    inline = parse_message((fixtures_dir / "html_inline_style.eml").read_bytes()).sanitized_html_body.lower()
    media = parse_message((fixtures_dir / "html_media_style.eml").read_bytes()).sanitized_html_body.lower()
    table = parse_message((fixtures_dir / "html_table_layout.eml").read_bytes()).sanitized_html_body.lower()
    malformed = parse_message(
        (fixtures_dir / "html_malformed_css.eml").read_bytes()
    ).sanitized_html_body.lower()

    assert ".brand{color:#123456;font-size:18px;padding:12px;}" in safe
    assert "font-weight:700 !important;" in safe

    assert ".safe{color:blue;}" in unsafe
    assert "@import" not in unsafe
    assert "@font-face" not in unsafe
    assert "tracker.example.test" not in unsafe
    assert "position:fixed" not in unsafe
    assert "z-index" not in unsafe

    assert "color:rgb(10, 20, 30);" in inline
    assert "padding:16px;" in inline
    assert "width:calc(100% - 20px);" in inline
    assert "background-image" not in inline
    assert "position:fixed" not in inline

    assert "@media screen and (max-width: 600px)" in media
    assert "prefers-color-scheme" not in media
    assert "@media only" not in media

    assert "width:600px;" in table
    assert "border-collapse:collapse;" in table
    assert "table-layout:fixed;" in table
    assert "background-color:#f4f4f4;" in table
    assert "vertical-align:top;" in table

    assert "malformed css must not break the message." in malformed
    assert "padding:10px;" in malformed
    assert "expression(" not in malformed


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
