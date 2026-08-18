from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib import messages as flash_messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F, Max, Q, Sum
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.http import content_disposition_header
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.audit.services import record_audit
from apps.core.access import (
    accessible_mailboxes,
    accessible_messages,
    user_can_delete_message,
)
from apps.mailboxes.validators import confined_path

from .models import Attachment
from .services import set_message_read_state, soft_delete_message


LIVE_UPDATE_HEADER = "X-MailStack-Live-Request"


def _message_preview(message, limit: int = 180) -> str:
    source = message.text_body or strip_tags(message.sanitized_html_body or "")
    normalized = " ".join(source.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


@login_required
def inbox(request, mailbox_uuid):
    mailbox = get_object_or_404(accessible_mailboxes(request.user), uuid=mailbox_uuid)
    queryset = (
        accessible_messages(request.user)
        .filter(mailbox=mailbox)
        .order_by(F("received_at").desc(nulls_last=True), "-created_at")
    )
    query = request.GET.get("q", "").strip()
    read_filter = request.GET.get("read", "")
    attachment_filter = request.GET.get("attachments", "")
    if query:
        queryset = queryset.filter(Q(sender_address__icontains=query) | Q(subject__icontains=query))
    if read_filter == "read":
        queryset = queryset.filter(is_read=True)
    elif read_filter == "unread":
        queryset = queryset.filter(is_read=False)
    if attachment_filter == "yes":
        queryset = queryset.filter(has_attachments=True)
    elif attachment_filter == "no":
        queryset = queryset.filter(has_attachments=False)
    page_obj = Paginator(queryset, 30).get_page(request.GET.get("page"))
    for item in page_obj.object_list:
        item.ui_preview = _message_preview(item)
    record_audit(
        "inbox_access", request=request, target_type="mailbox", target_identifier=mailbox.email_address
    )
    return render(
        request,
        "messages/inbox.html",
        {
            "mailbox": mailbox,
            "page_obj": page_obj,
            "query": query,
            "can_delete_mailbox": False,
            "live_unfiltered_first_page": not any(
                [query, read_filter, attachment_filter, request.GET.get("page") not in {None, "", "1"}]
            ),
        },
    )


@login_required
def message_detail(request, mailbox_uuid, message_uuid):
    message = get_object_or_404(
        accessible_messages(request.user).prefetch_related("attachments"),
        uuid=message_uuid,
        mailbox__uuid=mailbox_uuid,
    )
    message, _changed = set_message_read_state(message, is_read=True, actor=request.user, request=request)
    message = get_object_or_404(
        accessible_messages(request.user).prefetch_related("attachments"), pk=message.pk
    )
    record_audit(
        "message_view",
        request=request,
        target_type="message",
        target_identifier=str(message.uuid),
        details={"mailbox": message.mailbox.email_address},
    )
    return render(
        request,
        "messages/detail.html",
        {
            "mailbox": message.mailbox,
            "email_message": message,
            "can_delete_message": user_can_delete_message(request.user, message),
        },
    )


@login_required
@require_GET
def safe_html(request, message_uuid):
    message = get_object_or_404(accessible_messages(request.user), uuid=message_uuid)
    record_audit(
        "message_html_view", request=request, target_type="message", target_identifier=str(message.uuid)
    )
    body = message.sanitized_html_body or "<p>No HTML body is available.</p>"
    document = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<style>"
        "html{color:#172033;background:#fff;font-family:Arial,Helvetica,sans-serif;}"
        "body{margin:0;padding:20px;line-height:1.55;overflow-wrap:anywhere;}"
        "img{max-width:100%;height:auto;}table{max-width:100%;border-collapse:collapse;}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;}blockquote{margin-left:0;padding-left:14px;"
        "border-left:3px solid #d9e1ee;color:#475467;}a{color:#0b4ff5;}"
        "</style></head><body>"
        + body
        + "</body></html>"
    )
    response = HttpResponse(document, content_type="text/html; charset=utf-8")
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
@require_POST
def mark_state(request, mailbox_uuid, message_uuid):
    message = get_object_or_404(
        accessible_messages(request.user), uuid=message_uuid, mailbox__uuid=mailbox_uuid
    )
    desired = request.POST.get("state")
    if desired != "unread":
        raise PermissionDenied("Invalid read state")
    set_message_read_state(message, is_read=False, actor=request.user, request=request)
    return redirect("messages:inbox", mailbox_uuid=mailbox_uuid)


@login_required
@require_http_methods(["GET", "POST"])
def message_delete(request, mailbox_uuid, message_uuid):
    message = get_object_or_404(
        accessible_messages(request.user), uuid=message_uuid, mailbox__uuid=mailbox_uuid
    )
    if not user_can_delete_message(request.user, message):
        raise Http404("Message not found")
    if request.method == "POST":
        soft_delete_message(message, actor=request.user, request=request)
        flash_messages.success(request, "Message deleted. The source email remains preserved.")
        return redirect("messages:inbox", mailbox_uuid=mailbox_uuid)
    return render(
        request,
        "messages/confirm_delete.html",
        {"email_message": message, "mailbox": message.mailbox},
    )


@login_required
@require_GET
def attachment_download(request, mailbox_uuid, message_uuid, attachment_uuid):
    message = get_object_or_404(
        accessible_messages(request.user), uuid=message_uuid, mailbox__uuid=mailbox_uuid
    )
    attachment = get_object_or_404(Attachment, uuid=attachment_uuid, message=message)
    path = confined_path(settings.ATTACHMENT_STORAGE_ROOT, attachment.storage_relative_path)
    if not path.is_file():
        raise Http404("Attachment file is missing")
    record_audit(
        "attachment_download",
        request=request,
        target_type="attachment",
        target_identifier=str(attachment.uuid),
    )
    if getattr(settings, "USE_X_ACCEL_REDIRECT", False):
        response = HttpResponse(content_type="application/octet-stream")
        response["X-Accel-Redirect"] = f"/_protected_attachments/{attachment.storage_relative_path}"
    else:
        response = FileResponse(path.open("rb"), content_type="application/octet-stream")
    response["Content-Disposition"] = content_disposition_header(True, attachment.safe_filename)
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


def _iso(value):
    return value.isoformat() if value else None


@login_required
@require_GET
@never_cache
def live_updates(request):
    if request.headers.get(LIVE_UPDATE_HEADER) != "1":
        return redirect("dashboard:index")

    bootstrap = request.GET.get("bootstrap") == "1"
    try:
        cursor = max(0, int(request.GET.get("cursor", "0")))
    except (TypeError, ValueError):
        cursor = 0
    mailbox_qs = accessible_mailboxes(request.user)
    message_qs = accessible_messages(request.user)
    current_cursor = message_qs.aggregate(value=Max("id"))["value"] or 0
    new_messages = []
    next_cursor = current_cursor if bootstrap else cursor
    if not bootstrap:
        rows = list(message_qs.filter(id__gt=cursor).order_by("id")[: settings.LIVE_UPDATE_MESSAGE_LIMIT])
        for item in rows:
            new_messages.append(
                {
                    "id": item.id,
                    "uuid": str(item.uuid),
                    "mailbox_uuid": str(item.mailbox.uuid),
                    "mailbox": item.mailbox.email_address,
                    "sender_name": item.sender_name,
                    "sender_address": item.sender_address,
                    "subject": item.subject or "(No subject)",
                    "preview": _message_preview(item),
                    "received_at": _iso(item.received_at),
                    "size_bytes": item.size_bytes,
                    "has_attachments": item.has_attachments,
                    "is_read": item.is_read,
                    "detail_url": reverse("messages:detail", args=[item.mailbox.uuid, item.uuid]),
                }
            )
        if rows:
            next_cursor = rows[-1].id
    aggregates = mailbox_qs.aggregate(
        total_messages=Sum("total_messages"),
        total_unread=Sum("unread_messages"),
        last_received=Max("last_received_at"),
    )
    requested_mailbox_uuids = []
    for raw_uuid in request.GET.get("mailboxes", "").split(","):
        raw_uuid = raw_uuid.strip()
        if not raw_uuid:
            continue
        try:
            requested_mailbox_uuids.append(uuid.UUID(raw_uuid))
        except ValueError:
            continue
        if len(requested_mailbox_uuids) >= settings.LIVE_UPDATE_VISIBLE_MAILBOX_LIMIT:
            break

    mailbox_rows_qs = mailbox_qs
    if requested_mailbox_uuids:
        mailbox_rows_qs = mailbox_rows_qs.filter(uuid__in=requested_mailbox_uuids)
    mailbox_rows = list(
        mailbox_rows_qs.values(
            "uuid",
            "email_address",
            "status",
            "total_messages",
            "unread_messages",
            "last_received_at",
        ).order_by("email_address")[: settings.LIVE_UPDATE_MAILBOX_LIMIT]
    )
    payload = {
        "cursor": next_cursor,
        "has_more": bool(not bootstrap and next_cursor < current_cursor),
        "summary": {
            "total_mailboxes": mailbox_qs.count(),
            "active_mailboxes": mailbox_qs.filter(status="active").count(),
            "disabled_mailboxes": mailbox_qs.filter(status="disabled").count(),
            "total_messages": aggregates["total_messages"] or 0,
            "total_unread": aggregates["total_unread"] or 0,
            "last_received": _iso(aggregates["last_received"]),
        },
        "mailboxes_truncated": mailbox_qs.count() > settings.LIVE_UPDATE_MAILBOX_LIMIT,
        "mailboxes": [
            {
                **row,
                "uuid": str(row["uuid"]),
                "last_received_at": _iso(row["last_received_at"]),
            }
            for row in mailbox_rows
        ],
        "messages": new_messages,
    }
    response = JsonResponse(payload)
    response["Cache-Control"] = "private, no-store"
    return response
