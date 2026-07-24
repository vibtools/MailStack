from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.audit.services import record_audit
from apps.core.access import (
    accessible_mailboxes,
    is_admin,
    require_admin,
    user_can_delete_mailbox,
)

from .forms import MailboxCreateForm
from .models import Mailbox
from .services import ProvisioningError, provision_mailbox, set_mailbox_status, soft_delete_mailbox


@login_required
def mailbox_list(request):
    queryset = accessible_mailboxes(request.user)
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    if query:
        queryset = queryset.filter(Q(local_part__icontains=query) | Q(email_address__icontains=query))
    if status in {Mailbox.Status.ACTIVE, Mailbox.Status.DISABLED}:
        queryset = queryset.filter(status=status)
    page_obj = Paginator(queryset, 25).get_page(request.GET.get("page"))
    return render(
        request,
        "mailboxes/list.html",
        {"page_obj": page_obj, "query": query, "status": status, "is_admin": is_admin(request.user)},
    )


@login_required
@require_http_methods(["GET", "POST"])
def mailbox_create(request):
    form = MailboxCreateForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        assigned_users = (
            form.cleaned_data.get("assigned_users", [])
            if is_admin(request.user)
            else [request.user]
        )
        try:
            mailbox = provision_mailbox(
                form.cleaned_data["local_part"],
                actor=request.user,
                request=request,
                assigned_users=assigned_users,
            )
        except ProvisioningError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, f"Mailbox {mailbox.email_address} created.")
            return redirect("mailboxes:list")
    return render(request, "mailboxes/create.html", {"form": form, "is_admin": is_admin(request.user)})


@login_required
@require_POST
def mailbox_toggle(request, mailbox_uuid):
    require_admin(request.user)
    mailbox = get_object_or_404(accessible_mailboxes(request.user), uuid=mailbox_uuid)
    action = request.POST.get("action")
    if action == "enable":
        target, event, message = Mailbox.Status.ACTIVE, "mailbox_enable", "Mailbox enabled."
    elif action == "disable":
        target, event, message = Mailbox.Status.DISABLED, "mailbox_disable", "Mailbox disabled."
    else:
        messages.error(request, "Invalid mailbox action.")
        return redirect("mailboxes:list")
    try:
        set_mailbox_status(mailbox, target)
    except ProvisioningError as exc:
        messages.error(request, str(exc))
        return redirect("mailboxes:list")
    record_audit(event, request=request, target_type="mailbox", target_identifier=mailbox.email_address)
    messages.success(request, message)
    return redirect("mailboxes:list")


@login_required
@require_http_methods(["GET", "POST"])
def mailbox_delete(request, mailbox_uuid):
    mailbox = get_object_or_404(accessible_mailboxes(request.user), uuid=mailbox_uuid)
    if not user_can_delete_mailbox(request.user, mailbox):
        from django.http import Http404

        raise Http404("Mailbox not found")
    if request.method == "POST":
        confirmation = (request.POST.get("confirmation") or "").strip().lower()
        if confirmation != mailbox.email_address.lower():
            messages.error(request, "Type the full mailbox address to confirm deletion.")
        else:
            try:
                soft_delete_mailbox(mailbox, actor=request.user, request=request)
            except ProvisioningError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, f"Mailbox {mailbox.email_address} deleted and reserved.")
                return redirect("mailboxes:list")
    return render(request, "mailboxes/confirm_delete.html", {"mailbox": mailbox})
