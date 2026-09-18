from __future__ import annotations

from django.db import models
from django.utils import timezone


class ServiceHeartbeat(models.Model):
    service_name = models.CharField(max_length=80, unique=True)
    status = models.CharField(max_length=32, default="unknown")
    details = models.JSONField(default=dict, blank=True)
    last_seen_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.service_name}: {self.status}"


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=120, default="MailStack")
    site_tagline = models.CharField(max_length=200, default="Self-hosted mail server and shared team inbox.")
    logo = models.FileField(upload_to="site-settings/", blank=True)
    favicon = models.FileField(upload_to="site-settings/", blank=True)
    support_email = models.EmailField(default="")
    contact_phone = models.CharField(max_length=40, blank=True)
    office_address = models.CharField(max_length=255, blank=True)
    footer_description = models.TextField(blank=True)
    copyright_text = models.CharField(max_length=255, default="Authorized team use only.")
    source_code_url = models.URLField(default="https://github.com/vibtools/MailStack")
    privacy_url = models.CharField(max_length=500, default="/privacy/")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "site settings"
        verbose_name_plural = "site settings"

    def __str__(self) -> str:
        return self.site_name

    @classmethod
    def get_solo(cls):
        settings_object, _created = cls.objects.get_or_create(pk=1)
        return settings_object
