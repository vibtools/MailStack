from __future__ import annotations

from typing import cast

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from apps.mailboxes.models import Mailbox

from .models import UserAccessPolicy


class _BootstrapFormMixin:
    """Apply accessible local styling without changing Django authentication semantics."""

    def _style_fields(self) -> None:
        form = cast(forms.BaseForm, self)
        for field in form.fields.values():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                continue
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-control".strip()
            field.widget.attrs.setdefault("autocomplete", "off")


class SecureAuthenticationForm(_BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._style_fields()
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["password"].widget.attrs["autocomplete"] = "current-password"


class _CaseInsensitiveUsernameMixin:
    def clean_username(self):
        form = cast(forms.ModelForm, self)
        username = form.cleaned_data["username"].strip()
        user_model = get_user_model()
        existing = user_model._default_manager.filter(username__iexact=username)
        if form.instance.pk:
            existing = existing.exclude(pk=form.instance.pk)
        if existing.exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username


class UserCreateForm(_CaseInsensitiveUsernameMixin, _BootstrapFormMixin, UserCreationForm):
    assigned_mailboxes = forms.ModelMultipleChoiceField(
        queryset=Mailbox.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    can_delete_messages = forms.BooleanField(required=False)
    can_delete_mailboxes = forms.BooleanField(required=False)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "is_active", "password1", "password2")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        mailbox_field = cast(
            forms.ModelMultipleChoiceField, self.fields["assigned_mailboxes"]
        )
        mailbox_field.queryset = Mailbox.objects.filter(
            deleted_at__isnull=True
        ).order_by("email_address")
        self._style_fields()
        self.fields["username"].widget.attrs.update(
            {"placeholder": "e.g. alex.morgan", "spellcheck": "false", "autocomplete": "off"}
        )
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password1"].widget.attrs["placeholder"] = "••••••••••••"
        self.fields["password2"].widget.attrs["placeholder"] = "••••••••••••"

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class UserEditForm(_CaseInsensitiveUsernameMixin, _BootstrapFormMixin, forms.ModelForm):
    assigned_mailboxes = forms.ModelMultipleChoiceField(
        queryset=Mailbox.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    can_delete_messages = forms.BooleanField(required=False)
    can_delete_mailboxes = forms.BooleanField(required=False)

    class Meta:
        model = get_user_model()
        fields = ("username", "is_active")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        mailbox_field = cast(
            forms.ModelMultipleChoiceField, self.fields["assigned_mailboxes"]
        )
        mailbox_field.queryset = Mailbox.objects.filter(
            deleted_at__isnull=True
        ).order_by("email_address")
        if self.instance.pk:
            self.fields["assigned_mailboxes"].initial = self.instance.mailbox_memberships.values_list(
                "mailbox_id", flat=True
            )
            policy, _created = UserAccessPolicy.objects.get_or_create(user=self.instance)
            self.fields["can_delete_messages"].initial = policy.can_delete_messages
            self.fields["can_delete_mailboxes"].initial = policy.can_delete_mailboxes
        self._style_fields()
