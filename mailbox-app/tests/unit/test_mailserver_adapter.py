from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError

from apps.mailboxes import mailserver
from apps.mailboxes.mailserver import MailServerContractError
from apps.mailboxes.models import Mailbox
from apps.mailboxes.services import ProvisioningError, provision_mailbox, set_mailbox_status


def cursor_context(*, fetchone=None, fetchall=None, rowcount=1):
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone
    cursor.fetchall.return_value = fetchall or []
    cursor.rowcount = rowcount
    context = MagicMock()
    context.__enter__.return_value = cursor
    return context, cursor


def test_disabled_password_is_non_dovecot_hash_and_random():
    first = mailserver._disabled_password_hash()
    second = mailserver._disabled_password_hash()
    assert first.startswith("!VIBMAIL-READ-ONLY!")
    assert second.startswith("!VIBMAIL-READ-ONLY!")
    assert first != second
    assert len(first) < 255


def test_list_mailserver_mailboxes_maps_rows(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    context, cursor = cursor_context(
        fetchall=[("mailbox1", "mailbox1@example.com", "vibmail.my/mailbox1/Maildir/", 1)]
    )
    with patch("apps.mailboxes.mailserver.connection.cursor", return_value=context):
        rows = mailserver.list_mailserver_mailboxes()
    assert rows == [
        mailserver.MailServerMailbox(
            local_part="mailbox1",
            email="mailbox1@example.com",
            maildir="vibmail.my/mailbox1/Maildir/",
            active=True,
        )
    ]
    assert "`vibmail`.`mailboxes`" in cursor.execute.call_args.args[0]
    assert "WHERE d.name" not in cursor.execute.call_args.args[0]


def test_list_mailserver_mailboxes_filters_when_domain_is_requested(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    context, cursor = cursor_context()
    with patch("apps.mailboxes.mailserver.connection.cursor", return_value=context):
        mailserver.list_mailserver_mailboxes(domain_name="example.test")
    assert "WHERE d.name = %s" in cursor.execute.call_args.args[0]
    assert cursor.execute.call_args.args[1] == ["example.test"]


def test_mailserver_exists_and_disabled_mode(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = False
    assert mailserver.mailserver_mailbox_exists("mailbox1@example.com") is False
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    context, _cursor = cursor_context(fetchone=(1,))
    with patch("apps.mailboxes.mailserver.connection.cursor", return_value=context):
        assert mailserver.mailserver_mailbox_exists("mailbox1@example.com") is True


def test_mailserver_exists_scopes_explicit_domain(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    context, cursor = cursor_context(fetchone=(1,))
    with patch("apps.mailboxes.mailserver.connection.cursor", return_value=context):
        assert mailserver.mailserver_mailbox_exists(
            "mailbox1@example.com", domain_name="example.com"
        )
    assert "INNER JOIN" in cursor.execute.call_args.args[0]
    assert cursor.execute.call_args.args[1] == ["mailbox1@example.com", "example.com"]


def test_delete_mailserver_mailbox_requires_existing_row(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    context, cursor = cursor_context(rowcount=1)
    with patch("apps.mailboxes.mailserver.connection.cursor", return_value=context):
        mailserver.delete_mailserver_mailbox(email="mailbox1@example.com")
    assert "DELETE FROM" in cursor.execute.call_args.args[0]


def test_create_mailserver_mailbox_executes_expected_insert(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    alias_context, _alias_cursor = cursor_context(fetchone=None)
    create_context, create_cursor = cursor_context()
    create_cursor.fetchone.side_effect = [(1,), None]
    with patch(
        "apps.mailboxes.mailserver.connection.cursor",
        side_effect=[alias_context, create_context],
    ):
        mailserver.create_mailserver_mailbox(
            local_part="sales",
            email="sales@vibmail.my",
            maildir="vibmail.my/sales/Maildir/",
        )
    insert_call = create_cursor.execute.call_args_list[-1]
    assert "INSERT INTO `vibmail`.`mailboxes`" in insert_call.args[0]
    assert insert_call.args[1][1:3] == ["sales", "sales@vibmail.my"]
    assert insert_call.args[1][3].startswith("!VIBMAIL-READ-ONLY!")


def test_create_mailserver_mailbox_rejects_alias_source(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    context, _cursor = cursor_context(fetchone=(1,))
    with (
        patch("apps.mailboxes.mailserver.connection.cursor", return_value=context),
        pytest.raises(MailServerContractError, match="alias"),
    ):
        mailserver.create_mailserver_mailbox(
            local_part="postmaster",
            email="postmaster@vibmail.my",
            maildir="vibmail.my/postmaster/Maildir/",
        )


def test_create_mailserver_mailbox_requires_domain(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    alias_context, _alias_cursor = cursor_context(fetchone=None)
    create_context, create_cursor = cursor_context(fetchone=None)
    with (
        patch(
            "apps.mailboxes.mailserver.connection.cursor",
            side_effect=[alias_context, create_context],
        ),
        pytest.raises(MailServerContractError, match="domain"),
    ):
        mailserver.create_mailserver_mailbox(
            local_part="sales",
            email="sales@vibmail.my",
            maildir="vibmail.my/sales/Maildir/",
        )
    assert create_cursor.execute.call_count == 1


def test_status_service_calls_mailserver_adapter(mailbox, settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    with patch("apps.mailboxes.services.set_mailserver_mailbox_active") as update_remote:
        set_mailbox_status(mailbox, Mailbox.Status.DISABLED)
    update_remote.assert_called_once_with(email=mailbox.email_address, active=False)
    mailbox.refresh_from_db()
    assert mailbox.status == Mailbox.Status.DISABLED


def test_status_adapter_rejects_missing_mailbox(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    context, _cursor = cursor_context(rowcount=0)
    with (
        patch("apps.mailboxes.mailserver.connection.cursor", return_value=context),
        pytest.raises(MailServerContractError, match="missing"),
    ):
        mailserver.set_mailserver_mailbox_active(email="missing@vibmail.my", active=False)


@pytest.mark.django_db
def test_provisioning_calls_mailserver_inside_application_flow(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    with (
        patch("apps.mailboxes.services.mailserver_mailbox_exists", return_value=False) as exists_remote,
        patch("apps.mailboxes.services.create_mailserver_mailbox") as create_remote,
    ):
        mailbox = provision_mailbox("transactional")
    exists_remote.assert_called_once_with(email="transactional@vibmail.my", domain_name="vibmail.my")
    create_remote.assert_called_once_with(
        local_part="transactional",
        email="transactional@vibmail.my",
        maildir="vibmail.my/transactional/Maildir/",
        domain_name="vibmail.my",
    )
    assert mailbox.email_address == "transactional@vibmail.my"


@pytest.mark.django_db
def test_provisioning_cleans_up_remote_mailbox_when_database_save_fails(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    with (
        patch("apps.mailboxes.services.mailserver_mailbox_exists", return_value=False),
        patch("apps.mailboxes.services.create_mailserver_mailbox"),
        patch(
            "apps.mailboxes.services.Mailbox.save",
            side_effect=ValidationError("database failure"),
        ),
        patch("apps.mailboxes.services.delete_mailserver_mailbox") as delete_remote,
        pytest.raises(ProvisioningError, match="database failure"),
    ):
        provision_mailbox("remote-cleanup")
    delete_remote.assert_called_once_with(email="remote-cleanup@vibmail.my")


@pytest.mark.django_db
def test_provisioning_rejects_existing_mailserver_mailbox(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    with (
        patch("apps.mailboxes.services.mailserver_mailbox_exists", return_value=True),
        pytest.raises(ProvisioningError, match="already exists"),
    ):
        provision_mailbox("remote-existing")


def test_postfix_rows_uses_cross_schema_when_enabled(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    context, cursor = cursor_context(fetchall=[("mailbox1@example.com", "vibmail.my/mailbox1/Maildir/")])
    with patch("apps.mailboxes.mailserver.connection.cursor", return_value=context):
        rows = mailserver.postfix_rows()
    assert rows == [("mailbox1@example.com", "vibmail.my/mailbox1/Maildir/")]
    assert "`vibmail`.`postfix_virtual_mailboxes`" in cursor.execute.call_args.args[0]


def test_verify_mailserver_schema_counts_objects(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    context, cursor = cursor_context()
    cursor.fetchone.side_effect = [(1,), (4,), (3,)]
    with patch("apps.mailboxes.mailserver.connection.cursor", return_value=context):
        result = mailserver.verify_mailserver_schema()
    assert result == {"domains": 1, "mailboxes": 4, "postfix_rows": 3}


def test_verify_mailserver_schema_rejects_missing_domain(settings):
    settings.MAILSERVER_INTEGRATION_ENABLED = True
    context, _cursor = cursor_context(fetchone=(0,))
    with (
        patch("apps.mailboxes.mailserver.connection.cursor", return_value=context),
        pytest.raises(MailServerContractError, match="At least one"),
    ):
        mailserver.verify_mailserver_schema()
