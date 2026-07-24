from __future__ import annotations

from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.mailboxes.models import Mailbox
from apps.mailboxes.validators import confined_path, normalize_local_part, validate_local_part
from apps.messages.models import Attachment


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Mailbox1", "mailbox1"),
        ("  sales.team  ", "sales.team"),
        ("a", "a"),
        ("a_b-c.9", "a_b-c.9"),
    ],
)
def test_local_part_normalization_and_validation(value, expected):
    assert normalize_local_part(value) == expected
    assert validate_local_part(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "admin",
        "root",
        "postmaster",
        "abuse",
        ".start",
        "end.",
        "two..dots",
        "white space",
        "slash/name",
        r"back\\slash",
        "UPPER!",
        "a" * 65,
    ],
)
def test_local_part_rejects_invalid_and_reserved(value):
    with pytest.raises(ValidationError):
        validate_local_part(value)


def test_reserved_can_be_explicitly_allowed():
    assert validate_local_part("admin", allow_reserved=True) == "admin"
    assert validate_local_part("postmaster", allow_reserved=True) == "postmaster"


def test_confined_path_accepts_child_and_rejects_escape(tmp_path: Path):
    assert confined_path(tmp_path, "vibmail.my", "box") == (tmp_path / "vibmail.my" / "box").resolve()
    with pytest.raises(ValidationError):
        confined_path(tmp_path, "..", "escape")


@pytest.mark.django_db
def test_mailbox_model_normalizes_and_enforces_fixed_values():
    mailbox = Mailbox(
        local_part="Sales",
        email_address="sales@vibmail.my",
        maildir_relative_path="vibmail.my/sales/Maildir/",
    )
    mailbox.full_clean()
    assert mailbox.local_part == "sales"
    assert mailbox.email_address == "sales@vibmail.my"


@pytest.mark.django_db
def test_mailbox_model_rejects_mismatched_domain_and_path():
    mailbox = Mailbox(local_part="sales", email_address="sales@other.test", maildir_relative_path="wrong")
    with pytest.raises(ValidationError):
        mailbox.full_clean()


@pytest.mark.django_db
def test_case_insensitive_database_uniqueness(mailbox):
    with pytest.raises(IntegrityError), transaction.atomic():
        Mailbox.objects.create(
            local_part="MAILBOX1",
            email_address="mailbox1@example.com",
            maildir_relative_path="vibmail.my/mailbox1/Maildir/",
        )


@pytest.mark.django_db
def test_message_and_attachment_string_representations(message):
    attachment = Attachment.objects.create(
        message=message,
        original_filename="report.txt",
        safe_filename="report.txt",
        stored_filename="abc.bin",
        declared_mime_type="text/plain",
        detected_mime_type="text/plain",
        size_bytes=1,
        sha256="b" * 64,
        storage_relative_path="ab/abc.bin",
    )
    assert str(message) == "Test message"
    assert str(attachment) == "report.txt"
    message.subject = ""
    assert str(message) == "(No subject)"


def test_confined_path_rejects_symlink_component(settings, tmp_path):
    from apps.mailboxes.validators import confined_path

    target = settings.MAIL_STORAGE_ROOT / "safe-target"
    target.mkdir(parents=True)
    link = settings.MAIL_STORAGE_ROOT / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Symbolic links are unavailable in this test environment")
    with pytest.raises(ValidationError, match="Symbolic links"):
        confined_path(settings.MAIL_STORAGE_ROOT, "link", "mail")


@pytest.mark.django_db
def test_mailbox_model_accepts_authorized_reserved_system_address():
    mailbox = Mailbox(
        local_part="postmaster",
        email_address="postmaster@vibmail.my",
        maildir_relative_path="vibmail.my/postmaster/Maildir/",
    )
    mailbox.full_clean()
    assert mailbox.local_part == "postmaster"
