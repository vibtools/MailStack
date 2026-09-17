from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.mailboxes.mailserver import MailServerMailbox
from apps.mailboxes.models import Mailbox


def test_sync_mailserver_mailboxes_imports_existing_row(db, settings):
    source = MailServerMailbox(
        local_part="mailbox1",
        email=f"mailbox1@{settings.MAIL_DOMAIN}",
        maildir=f"{settings.MAIL_DOMAIN}/mailbox1/Maildir/",
        active=True,
    )
    with patch(
        "apps.mailboxes.management.commands.sync_mailserver_mailboxes.list_mailserver_mailboxes",
        return_value=[source],
    ):
        call_command("sync_mailserver_mailboxes", "--strict")
    mailbox = Mailbox.objects.get(local_part="mailbox1")
    assert mailbox.email_address == source.email
    assert mailbox.maildir_relative_path == source.maildir
    assert mailbox.status == Mailbox.Status.ACTIVE


def test_sync_mailserver_mailboxes_updates_status(db, mailbox):
    source = MailServerMailbox(
        local_part=mailbox.local_part,
        email=mailbox.email_address,
        maildir=mailbox.maildir_relative_path,
        active=False,
    )
    with patch(
        "apps.mailboxes.management.commands.sync_mailserver_mailboxes.list_mailserver_mailboxes",
        return_value=[source],
    ):
        call_command("sync_mailserver_mailboxes", "--strict")
    mailbox.refresh_from_db()
    assert mailbox.status == Mailbox.Status.DISABLED


def test_sync_mailserver_mailboxes_rejects_unsafe_source_domain(db):
    source = MailServerMailbox(
        local_part="mailbox1",
        email="mailbox1@bad domain.test",
        maildir="bad domain.test/mailbox1/Maildir/",
        active=True,
    )
    with (
        patch(
            "apps.mailboxes.management.commands.sync_mailserver_mailboxes.list_mailserver_mailboxes",
            return_value=[source],
        ),
        pytest.raises(CommandError, match="invalid source rows"),
    ):
        call_command("sync_mailserver_mailboxes", "--strict")


def test_sync_mailserver_mailboxes_disables_unverified_domain(db, settings):
    source = MailServerMailbox(
        local_part="secondary",
        email="secondary@example.test",
        maildir="example.test/secondary/Maildir/",
        active=True,
    )
    with (
        patch(
            "apps.mailboxes.management.commands.sync_mailserver_mailboxes.list_mailserver_mailboxes",
            return_value=[source],
        ),
        patch(
            "apps.mailboxes.management.commands.sync_mailserver_mailboxes.ensure_mailserver_domain"
        ) as ensure_domain,
    ):
        call_command("sync_mailserver_mailboxes", "--strict")
    mailbox = Mailbox.objects.get(email_address=source.email)
    assert mailbox.status == Mailbox.Status.DISABLED
    ensure_domain.assert_called_once_with(domain_name="example.test", active=False)
