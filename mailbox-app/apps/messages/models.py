from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Message(models.Model):
    class ParseStatus(models.TextChoices):
        OK = "ok", "OK"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        OVERSIZED = "oversized", "Oversized"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    mailbox = models.ForeignKey("mailboxes.Mailbox", on_delete=models.CASCADE, related_name="messages")
    source_file_key = models.CharField(max_length=1024)
    source_sha256 = models.CharField(max_length=64)
    message_id_header = models.CharField(max_length=998, blank=True)
    sender_name = models.CharField(max_length=500, blank=True)
    sender_address = models.CharField(max_length=320, blank=True, db_index=True)
    recipient_addresses = models.JSONField(default=list, blank=True)
    cc_addresses = models.JSONField(default=list, blank=True)
    subject = models.CharField(max_length=998, blank=True, db_index=True)
    received_at = models.DateTimeField(null=True, blank=True)
    parsed_at = models.DateTimeField()
    text_body = models.TextField(blank=True)
    sanitized_html_body = models.TextField(blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    is_read = models.BooleanField(default=False, db_index=True)
    has_attachments = models.BooleanField(default=False)
    parse_status = models.CharField(
        max_length=16, choices=ParseStatus.choices, default=ParseStatus.OK, db_index=True
    )
    parse_warning = models.TextField(blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_received_messages",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-received_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["mailbox", "source_file_key"], name="message_source_per_mailbox_unique"
            )
        ]
        indexes = [
            models.Index(fields=["mailbox", "-received_at"]),
            models.Index(fields=["mailbox", "is_read"]),
            models.Index(fields=["mailbox", "has_attachments"]),
            models.Index(fields=["mailbox", "deleted_at", "is_read"]),
            models.Index(fields=["deleted_at", "id"]),
            models.Index(fields=["parse_status"]),
        ]

    def __str__(self) -> str:
        return self.subject or "(No subject)"


class Attachment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    original_filename = models.CharField(max_length=1000, blank=True)
    safe_filename = models.CharField(max_length=255)
    stored_filename = models.CharField(max_length=255, unique=True)
    declared_mime_type = models.CharField(max_length=255, blank=True)
    detected_mime_type = models.CharField(max_length=255, blank=True)
    size_bytes = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    storage_relative_path = models.CharField(max_length=500, unique=True)
    is_inline = models.BooleanField(default=False)
    content_id = models.CharField(max_length=998, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.safe_filename
