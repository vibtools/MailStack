from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower

from .validators import validate_local_part


class Mailbox(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DISABLED = "disabled", "Disabled"
        DELETED = "deleted", "Deleted"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    local_part = models.CharField(max_length=64, unique=True)
    email_address = models.EmailField(max_length=320, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    maildir_relative_path = models.CharField(max_length=255)
    total_messages = models.PositiveBigIntegerField(default=0)
    unread_messages = models.PositiveBigIntegerField(default=0)
    last_received_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_mailboxes",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["local_part"]
        constraints = [
            models.UniqueConstraint(Lower("local_part"), name="mailbox_local_part_ci_unique"),
            models.UniqueConstraint(Lower("email_address"), name="mailbox_email_address_ci_unique"),
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "disabled", "deleted"]),
                name="mailbox_valid_status",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["deleted_at", "status"]),
        ]

    def clean(self) -> None:
        normalized = validate_local_part(self.local_part, allow_reserved=True)
        self.local_part = normalized
        domain = settings.MAIL_DOMAIN.strip().lower()
        expected_email = f"{normalized}@{domain}"
        expected_path = f"{domain}/{normalized}/Maildir/"
        if self.email_address and self.email_address.lower() != expected_email:
            raise ValidationError(
                {"email_address": f"Email address must match the configured {domain} domain."}
            )
        if self.maildir_relative_path and self.maildir_relative_path != expected_path:
            raise ValidationError(
                {"maildir_relative_path": "Maildir path does not match the mailbox local part."}
            )
        self.email_address = expected_email
        self.maildir_relative_path = expected_path

    def __str__(self) -> str:
        return self.email_address


class MailboxMembership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailbox_memberships",
    )
    mailbox = models.ForeignKey(Mailbox, on_delete=models.CASCADE, related_name="memberships")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mailbox_assignments_made",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "mailbox"], name="mailbox_membership_unique")
        ]
        indexes = [
            models.Index(fields=["user", "mailbox"]),
            models.Index(fields=["mailbox", "user"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.get_username()} -> {self.mailbox.email_address}"
