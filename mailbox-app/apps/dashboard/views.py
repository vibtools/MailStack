from __future__ import annotations

import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import connection, models
from django.shortcuts import render

from apps.core.access import accessible_mailboxes, accessible_messages, is_admin
from apps.core.models import ServiceHeartbeat
from apps.mailboxes.models import Mailbox


def _database_ok() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:
        return False


def _storage_ok(path) -> bool:
    try:
        return path.is_dir() and os.access(path, os.R_OK | os.W_OK | os.X_OK)
    except OSError:
        return False


@login_required
def index(request):
    mailboxes = accessible_mailboxes(request.user)
    messages = accessible_messages(request.user)
    administrator = is_admin(request.user)
    context = {
        "total_mailboxes": mailboxes.count(),
        "active_mailboxes": mailboxes.filter(status=Mailbox.Status.ACTIVE).count(),
        "disabled_mailboxes": mailboxes.filter(status=Mailbox.Status.DISABLED).count(),
        "total_messages": messages.count(),
        "total_unread": messages.filter(is_read=False).count(),
        "last_received": messages.aggregate(latest=models.Max("received_at"))["latest"],
        "recent_messages": messages.select_related("mailbox")[:8],
        "recent_mailboxes": mailboxes.order_by("-created_at")[:8],
        "is_admin": administrator,
    }
    if administrator:
        context.update(
            {
                "ingestion": ServiceHeartbeat.objects.filter(service_name="maildir_ingestion").first(),
                "mail_storage_ok": _storage_ok(settings.MAIL_STORAGE_ROOT),
                "database_ok": _database_ok(),
            }
        )
    return render(request, "dashboard/index.html", context)
