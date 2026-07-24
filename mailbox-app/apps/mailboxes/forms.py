from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model

from apps.core.access import is_admin

from .models import Mailbox
from .validators import validate_local_part


class MailboxCreateForm(forms.Form):
    local_part = forms.CharField(max_length=64, label="Mailbox local part")
    assigned_users = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.none(),
        required=False,
        label="Assign to users",
        widget=forms.SelectMultiple(attrs={"size": 8}),
    )

    def __init__(self, *args, user=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = user
        if is_admin(user):
            self.fields["assigned_users"].queryset = get_user_model().objects.filter(
                is_active=True, is_staff=False, is_superuser=False
            ).order_by("username")
        else:
            self.fields.pop("assigned_users")
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-control".strip()

    def clean_local_part(self):
        value = validate_local_part(self.cleaned_data["local_part"])
        if Mailbox.objects.filter(local_part__iexact=value).exists():
            raise forms.ValidationError("A mailbox with this local part already exists or is reserved.")
        return value
