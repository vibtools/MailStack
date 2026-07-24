from __future__ import annotations

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.mailboxes.services import provision_mailbox
from apps.messages.models import Message


@pytest.fixture(autouse=True)
def isolated_storage(settings, tmp_path: Path):
    settings.MAIL_STORAGE_ROOT = tmp_path / "vmail"
    settings.ATTACHMENT_STORAGE_ROOT = tmp_path / "attachments"
    settings.INGESTION_LOCK_FILE = tmp_path / "runtime" / "ingestion.lock"
    settings.LOG_DIRECTORY = tmp_path / "logs"
    settings.MAIL_STORAGE_ROOT.mkdir(parents=True)
    settings.ATTACHMENT_STORAGE_ROOT.mkdir(parents=True)
    yield


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_user(
        username="administrator",
        password="Secure-Test-Password-2026!",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def mailbox(db):
    return provision_mailbox("mailbox1")


@pytest.fixture
def message(mailbox):
    return Message.objects.create(
        mailbox=mailbox,
        source_file_key="new/test-message",
        source_sha256="a" * 64,
        message_id_header="<test@example.test>",
        sender_name="Test Sender",
        sender_address="sender@example.test",
        recipient_addresses=[mailbox.email_address],
        cc_addresses=["cc@example.test"],
        subject="Test message",
        received_at=timezone.now(),
        parsed_at=timezone.now(),
        text_body="Plain body",
        sanitized_html_body="<p>Safe body</p>",
        size_bytes=128,
    )


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"
