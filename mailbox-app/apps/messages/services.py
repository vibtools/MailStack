from __future__ import annotations

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.audit.services import record_audit
from apps.mailboxes.models import Mailbox

from .models import Message


def recalculate_mailbox_counters(mailbox: Mailbox | int) -> Mailbox:
    mailbox_id = mailbox.pk if isinstance(mailbox, Mailbox) else int(mailbox)
    locked = Mailbox.objects.select_for_update().get(pk=mailbox_id)
    queryset = Message.objects.filter(mailbox_id=mailbox_id, deleted_at__isnull=True)
    locked.total_messages = queryset.count()
    locked.unread_messages = queryset.filter(is_read=False).count()
    locked.last_received_at = queryset.aggregate(latest=Max("received_at"))["latest"]
    locked.save(update_fields=["total_messages", "unread_messages", "last_received_at", "updated_at"])
    return locked


def set_message_read_state(
    message: Message, *, is_read: bool, actor=None, request=None
) -> tuple[Message, bool]:
    with transaction.atomic():
        locked = Message.objects.select_for_update().select_related("mailbox").get(pk=message.pk)
        if locked.deleted_at is not None:
            return locked, False
        changed = locked.is_read != is_read
        if changed:
            locked.is_read = is_read
            locked.save(update_fields=["is_read", "updated_at"])
            recalculate_mailbox_counters(locked.mailbox_id)
    if changed:
        record_audit(
            "message_auto_read" if is_read else "message_mark_unread",
            request=request,
            actor=actor,
            target_type="message",
            target_identifier=str(locked.uuid),
            details={"mailbox": locked.mailbox.email_address},
        )
    return locked, changed


def soft_delete_message(message: Message, *, actor=None, request=None) -> tuple[Message, bool]:
    with transaction.atomic():
        locked = Message.objects.select_for_update().select_related("mailbox").get(pk=message.pk)
        changed = locked.deleted_at is None
        if changed:
            locked.deleted_at = timezone.now()
            locked.deleted_by = actor if getattr(actor, "is_authenticated", False) else None
            locked.save(update_fields=["deleted_at", "deleted_by", "updated_at"])
            recalculate_mailbox_counters(locked.mailbox_id)
    if changed:
        record_audit(
            "message_deleted",
            request=request,
            actor=actor,
            target_type="message",
            target_identifier=str(locked.uuid),
            details={"mailbox": locked.mailbox.email_address, "source_preserved": True},
        )
    return locked, changed
