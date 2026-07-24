from __future__ import annotations

from django.core.exceptions import PermissionDenied


def is_admin(user) -> bool:
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
    )


def require_admin(user) -> None:
    if not is_admin(user):
        raise PermissionDenied("Administrator access is required.")


def accessible_mailboxes(user, *, include_deleted: bool = False):
    from apps.mailboxes.models import Mailbox

    queryset = Mailbox.objects.all()
    if not include_deleted:
        queryset = queryset.filter(deleted_at__isnull=True)
    if is_admin(user):
        return queryset
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return queryset.none()
    return queryset.filter(memberships__user=user).distinct()


def accessible_messages(user, *, include_deleted: bool = False):
    from apps.messages.models import Message

    queryset = Message.objects.select_related("mailbox")
    if not include_deleted:
        queryset = queryset.filter(deleted_at__isnull=True, mailbox__deleted_at__isnull=True)
    if is_admin(user):
        return queryset
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return queryset.none()
    return queryset.filter(mailbox__memberships__user=user).distinct()


def _policy(user):
    from apps.accounts.models import UserAccessPolicy

    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return None
    policy, _created = UserAccessPolicy.objects.get_or_create(user=user)
    return policy


def user_can_delete_message(user, message) -> bool:
    if is_admin(user):
        return True
    policy = _policy(user)
    if not policy or not policy.can_delete_messages:
        return False
    return message.mailbox.memberships.filter(user=user).exists() and message.deleted_at is None


def user_can_delete_mailbox(user, mailbox) -> bool:
    if is_admin(user):
        return True
    policy = _policy(user)
    if not policy or not policy.can_delete_mailboxes:
        return False
    return mailbox.memberships.filter(user=user).exists() and mailbox.deleted_at is None
