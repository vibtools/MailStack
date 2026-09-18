from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.core.models import SiteSettings


def test_site_settings_is_admin_only(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("dashboard:site_settings"))
    assert response.status_code == 200
    assert "Site Settings" in response.content.decode()

    member = get_user_model().objects.create_user(username="member", password="Secure-Test-Password-2026!")
    client.force_login(member)
    assert client.get(reverse("dashboard:site_settings")).status_code == 403


def test_site_settings_persists_and_is_available_in_public_api(client, admin_user, settings):
    client.force_login(admin_user)
    response = client.post(reverse("dashboard:site_settings"), {
        "site_name": "Vib Mail",
        "site_tagline": "Private team inbox",
        "support_email": "support@example.test",
        "contact_phone": "+880 1000 000000",
        "office_address": "Dhaka",
        "footer_description": "Managed inbound mail.",
        "copyright_text": "Copyright 2026 Vib Mail",
        "source_code_url": "https://github.com/vibtools/MailStack",
        "privacy_url": "/privacy/",
    })
    assert response.status_code == 302
    assert SiteSettings.objects.get().site_name == "Vib Mail"

    api_response = client.get(reverse("core:site_settings_api"), HTTP_ORIGIN=settings.PUBLIC_SITE_ORIGIN)
    assert api_response.status_code == 200
    assert api_response.json()["site_name"] == "Vib Mail"
    assert api_response["Access-Control-Allow-Origin"] == settings.PUBLIC_SITE_ORIGIN


def test_site_settings_api_rejects_unconfigured_cors_origin(client, settings):
    response = client.get(reverse("core:site_settings_api"), HTTP_ORIGIN="https://untrusted.example")
    assert "Access-Control-Allow-Origin" not in response


def test_site_settings_rejects_non_image_uploads(client, admin_user):
    client.force_login(admin_user)
    response = client.post(reverse("dashboard:site_settings"), {
        "site_name": "MailStack",
        "site_tagline": "Inbound mail",
        "support_email": "support@example.test",
        "copyright_text": "Copyright",
        "source_code_url": "https://github.com/vibtools/MailStack",
        "privacy_url": "/privacy/",
        "logo": SimpleUploadedFile("logo.txt", b"not an image", content_type="text/plain"),
    })
    assert response.status_code == 200
    assert "supported image file" in response.content.decode()
