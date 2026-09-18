from __future__ import annotations

from typing import cast
from unittest.mock import patch

import pytest
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.mailboxes.dns import _decode_name, verify_dns_records, verify_domain
from apps.mailboxes.forms import DomainForm, MailboxCreateForm
from apps.mailboxes.mailserver import MailServerContractError
from apps.mailboxes.models import Domain, Mailbox
from apps.mailboxes.services import ProvisioningError, provision_mailbox
from apps.mailboxes.validators import validate_domain


@pytest.mark.parametrize("value", ["127.0.0.1", "bad domain.test", "-bad.test", "bad_.test"])
def test_domain_validation_rejects_unsafe_names(value):
    with pytest.raises(ValidationError):
        validate_domain(value)


def test_dns_verification_normalizes_records(settings):
    def resolver(name, record_type):
        if record_type == 15:
            return ["MAIL.VIBMAIL.MY."]
        return ["192.0.2.10"]

    result = verify_domain("Example.test", mail_hostname="mail.vibmail.my", resolver=resolver)
    assert result["verified"] is True
    assert result["mx_ok"] is True
    assert result["target_ok"] is True


def test_dns_record_verification_reports_each_record(settings):
    records = [
        {"type": "MX", "host": "example.test", "value": "mail.example.test", "copyable": True},
        {"type": "TXT", "host": "example.test", "value": "v=spf1 -all", "copyable": True},
    ]
    with patch("apps.mailboxes.dns.build_dns_records", return_value=records):
        result = verify_dns_records(
            "example.test",
            resolver=lambda name, record_type: (
                ["mail.example.test."] if record_type == 15 else ["unexpected"]
            ),
        )
    assert result["verified"] is False
    verified_records = cast(list[dict[str, object]], result["records"])
    assert [record["status"] for record in verified_records] == ["verified", "missing"]


def test_dns_compressed_name_decodes_without_pointer_offset_bug():
    packet = b"\x04mail\x04test\x00\xc0\x00"
    assert _decode_name(packet, 11) == "mail.test."


@pytest.mark.django_db
def test_same_local_part_is_allowed_in_different_verified_domains():
    first = Domain.objects.get(name="vibmail.my")
    second = Domain.objects.create(
        name="example.test", verification_status=Domain.VerificationStatus.VERIFIED
    )
    provision_mailbox("support", domain=first)
    other = provision_mailbox("support", domain=second)
    assert other.email_address == "support@example.test"
    assert Mailbox.objects.filter(local_part="support").count() == 2


@pytest.mark.django_db
def test_disabled_or_unverified_domains_cannot_provision():
    domain = Domain.objects.create(name="pending.test")
    with pytest.raises(ProvisioningError, match="active, DNS-verified"):
        provision_mailbox("support", domain=domain)


@pytest.mark.django_db
def test_mailbox_form_only_lists_active_verified_domains():
    form = MailboxCreateForm()
    domain_field = cast(forms.ModelChoiceField, form.fields["domain"])
    assert domain_field.queryset is not None
    domain_queryset = domain_field.queryset
    assert list(domain_queryset.values_list("name", flat=True)) == ["vibmail.my"]
    Domain.objects.create(name="disabled.test", status=Domain.Status.DISABLED, verification_status="verified")
    assert list(domain_queryset.values_list("name", flat=True)) == ["vibmail.my"]


@pytest.mark.django_db
def test_domain_list_requires_admin(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("mailboxes:domains"))
    assert response.status_code == 200
    assert b"Domains" in response.content


@pytest.mark.django_db
def test_domain_create_starts_with_empty_dns_table(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("mailboxes:domain_create"))
    assert response.status_code == 200
    assert b"No DNS records generated yet" in response.content


@pytest.mark.django_db
def test_domain_dns_preview_returns_records_for_valid_domain(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("mailboxes:domain_dns_preview"), {"domain": "example.test"})
    assert response.status_code == 200
    assert response.json()["records"][0]["type"] == "MX"


@pytest.mark.django_db
def test_domain_create_requires_dns_confirmation(client, admin_user):
    client.force_login(admin_user)
    response = client.post(
        reverse("mailboxes:domain_create"),
        {"name": "unconfirmed.test", "status": Domain.Status.DISABLED},
    )
    assert response.status_code == 200
    assert not Domain.objects.filter(name="unconfirmed.test").exists()
    assert b"Confirm that all DNS records" in response.content


@pytest.mark.django_db
def test_existing_domain_cannot_be_renamed():
    domain = Domain.objects.get(name="vibmail.my")
    form = DomainForm(instance=domain, data={"name": "renamed.test", "status": domain.status})
    assert not form.is_valid()
    assert "cannot be changed" in str(form.errors)


@pytest.mark.django_db
def test_unverified_domain_cannot_be_enabled():
    domain = Domain.objects.create(name="pending-enable.test")
    form = DomainForm(instance=domain, data={"name": domain.name, "status": Domain.Status.ACTIVE})
    assert not form.is_valid()
    assert "pass DNS verification" in str(form.errors)


@pytest.mark.django_db
def test_failed_dns_check_disables_delivery(client, admin_user):
    client.force_login(admin_user)
    domain = Domain.objects.get(name="vibmail.my")
    with (
        patch(
            "apps.mailboxes.views.verify_domain",
            return_value={"verified": False, "message": "MX record mismatch"},
        ),
        patch("apps.mailboxes.views.set_mailserver_domain_active") as disable_domain,
    ):
        response = client.post(reverse("mailboxes:domain_check", args=[domain.uuid]))
    assert response.status_code == 302
    disable_domain.assert_called_once_with(domain_name=domain.name, active=False)
    domain.refresh_from_db()
    assert domain.status == Domain.Status.DISABLED
    assert domain.verification_status == Domain.VerificationStatus.FAILED


@pytest.mark.django_db
def test_empty_secondary_domain_can_be_removed(client, admin_user):
    client.force_login(admin_user)
    domain = Domain.objects.create(
        name="remove.test", verification_status=Domain.VerificationStatus.VERIFIED
    )
    response = client.post(reverse("mailboxes:domain_delete", args=[domain.uuid]))
    assert response.status_code == 302
    assert not Domain.objects.filter(pk=domain.pk).exists()


@pytest.mark.django_db
def test_default_domain_cannot_be_removed(client, admin_user):
    client.force_login(admin_user)
    domain = Domain.objects.create(
        name="default.test",
        is_default=True,
        verification_status=Domain.VerificationStatus.VERIFIED,
    )
    response = client.post(reverse("mailboxes:domain_delete", args=[domain.uuid]))
    assert response.status_code == 302
    assert Domain.objects.filter(pk=domain.pk).exists()


@pytest.mark.django_db
def test_domain_create_propagates_disabled_status_to_mailserver(client, admin_user):
    client.force_login(admin_user)
    with patch("apps.mailboxes.views.ensure_mailserver_domain") as ensure_domain:
        response = client.post(
            reverse("mailboxes:domain_create"),
            {
                "name": "disabled.test",
                "status": Domain.Status.DISABLED,
                "dns_confirmed": "1",
            },
        )
    assert response.status_code == 302
    ensure_domain.assert_called_once_with(domain_name="disabled.test", active=False)


@pytest.mark.django_db
def test_domain_edit_rejects_mailserver_reconciliation_failure(client, admin_user):
    client.force_login(admin_user)
    domain = Domain.objects.get(name="vibmail.my")
    with patch(
        "apps.mailboxes.views.ensure_mailserver_domain",
        side_effect=MailServerContractError("mail server unavailable"),
    ):
        response = client.post(
            reverse("mailboxes:domain_edit", args=[domain.uuid]),
            {"name": domain.name, "status": Domain.Status.DISABLED},
        )
    assert response.status_code == 200
    domain.refresh_from_db()
    assert domain.status == Domain.Status.ACTIVE
