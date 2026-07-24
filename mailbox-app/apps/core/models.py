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
