from __future__ import annotations

from django import forms

from .models import SiteSettings


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = (
            "site_name", "site_tagline", "logo", "favicon", "support_email", "contact_phone",
            "office_address", "footer_description", "copyright_text", "source_code_url", "privacy_url",
        )
        widgets = {
            "logo": forms.ClearableFileInput(
                attrs={"accept": "image/gif,image/jpeg,image/png,image/svg+xml,image/webp"}
            ),
            "favicon": forms.ClearableFileInput(
                attrs={"accept": "image/gif,image/x-icon,image/png,image/svg+xml,image/webp"}
            ),
            "footer_description": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if logo and logo.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Logo must be 2 MB or smaller.")
        if logo and logo.content_type not in {
            "image/gif", "image/jpeg", "image/png", "image/svg+xml", "image/webp"
        }:
            raise forms.ValidationError("Logo must be a supported image file.")
        return logo

    def clean_favicon(self):
        favicon = self.cleaned_data.get("favicon")
        if favicon and favicon.size > 512 * 1024:
            raise forms.ValidationError("Favicon must be 512 KB or smaller.")
        if favicon and favicon.content_type not in {
            "image/gif", "image/x-icon", "image/png", "image/svg+xml", "image/webp"
        }:
            raise forms.ValidationError("Favicon must be a supported image file.")
        return favicon
