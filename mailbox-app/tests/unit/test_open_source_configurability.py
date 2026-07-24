from unittest.mock import patch

import pytest
from django.core.management import call_command

from apps.mailboxes.mailserver import MailServerMailbox
from apps.mailboxes.models import Mailbox


@pytest.mark.django_db
def test_mailbox_model_uses_configured_domain(settings):
    settings.MAIL_DOMAIN = "example.org"
    mailbox = Mailbox(local_part="support")
    mailbox.clean()
    assert mailbox.email_address == "support@example.org"
    assert mailbox.maildir_relative_path == "example.org/support/Maildir/"


@pytest.mark.django_db
def test_sync_command_uses_configured_domain(settings):
    settings.MAIL_DOMAIN = "example.org"
    source = MailServerMailbox(
        local_part="support",
        email="support@example.org",
        maildir="example.org/support/Maildir/",
        active=True,
    )
    with patch(
        "apps.mailboxes.management.commands.sync_mailserver_mailboxes.list_mailserver_mailboxes",
        return_value=[source],
    ):
        call_command("sync_mailserver_mailboxes", "--strict")
    assert Mailbox.objects.filter(email_address="support@example.org").exists()
