from __future__ import annotations

from typing import cast

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.core.access import is_admin

from .models import Domain, Mailbox
from .validators import validate_local_part


class DomainForm(forms.ModelForm):
    class Meta:
        model = Domain
        fields = ("name", "status")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["status"].initial = Domain.Status.DISABLED

    def clean_name(self):
        from .validators import validate_domain

        name = validate_domain(self.cleaned_data["name"])
        if self.instance.pk and name != self.instance.name:
            raise forms.ValidationError(
                "Domain names cannot be changed after creation; add a new domain instead."
            )
        return name

    def clean_status(self):
        status = self.cleaned_data["status"]
        if (
            status == Domain.Status.ACTIVE
            and self.instance.verification_status != Domain.VerificationStatus.VERIFIED
        ):
            raise forms.ValidationError("A domain must pass DNS verification before it can be enabled.")
        return status


class MailboxCreateForm(forms.Form):
    domain = forms.ModelChoiceField(queryset=Domain.objects.none(), label="Domain", required=False)
    local_part = forms.CharField(max_length=64, label="Mailbox local part")
    assigned_users = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.none(),
        required=False,
        label="Assign to users",
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, user=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = user
        cast(forms.ModelChoiceField, self.fields["domain"]).queryset = Domain.objects.filter(
            status=Domain.Status.ACTIVE, verification_status=Domain.VerificationStatus.VERIFIED
        ).order_by("name")
        if is_admin(user):
            assigned_users_field = cast(
                forms.ModelMultipleChoiceField, self.fields["assigned_users"]
            )
            assigned_users_field.queryset = get_user_model().objects.filter(
                is_active=True, is_staff=False, is_superuser=False
            ).order_by("username")
        else:
            self.fields.pop("assigned_users")
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                continue
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-control".strip()
        self.fields["local_part"].widget.attrs.update(
            {"autocomplete": "off", "placeholder": "e.g. logan.rodriguez", "spellcheck": "false"}
        )

    def clean_local_part(self):
        value = validate_local_part(self.cleaned_data["local_part"])
        domain = self.cleaned_data.get("domain") or Domain.objects.get_or_create(
            name=settings.MAIL_DOMAIN.strip().lower(),
            defaults={
                "status": Domain.Status.ACTIVE,
                "verification_status": Domain.VerificationStatus.VERIFIED,
            },
        )[0]
        if domain and Mailbox.objects.filter(domain=domain, local_part__iexact=value).exists():
            raise forms.ValidationError("A mailbox with this local part already exists or is reserved.")
        return value

    def clean_domain(self):
        return self.cleaned_data.get("domain")
