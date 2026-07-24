from __future__ import annotations

from django.conf import settings
from django.db import models


class LoginAttempt(models.Model):
    username_normalized = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    succeeded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["username_normalized", "ip_address", "created_at"])]


class UserAccessPolicy(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vibmail_access_policy",
    )
    can_delete_messages = models.BooleanField(default=False)
    can_delete_mailboxes = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Access policy for {self.user.get_username()}"
