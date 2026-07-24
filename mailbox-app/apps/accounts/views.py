from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from apps.audit.services import client_ip, record_audit
from apps.core.access import require_admin
from apps.mailboxes.models import MailboxMembership

from .forms import SecureAuthenticationForm, UserCreateForm, UserEditForm
from .models import LoginAttempt, UserAccessPolicy


def _attempts(username: str, ip_address: str | None):
    return LoginAttempt.objects.filter(username_normalized=username.lower(), ip_address=ip_address)


def _locked(username: str, ip_address: str | None) -> bool:
    now = timezone.now()
    window_start = now - timedelta(seconds=settings.LOGIN_FAILURE_WINDOW_SECONDS)
    recent_failures = _attempts(username, ip_address).filter(succeeded=False, created_at__gte=window_start)
    if recent_failures.count() < settings.LOGIN_FAILURE_LIMIT:
        return False
    latest_failure = recent_failures.order_by("-created_at").values_list("created_at", flat=True).first()
    return bool(latest_failure and latest_failure + timedelta(seconds=settings.LOGIN_LOCKOUT_SECONDS) > now)


def _prune_login_attempts() -> None:
    retention = max(settings.LOGIN_FAILURE_WINDOW_SECONDS, settings.LOGIN_LOCKOUT_SECONDS) * 8
    LoginAttempt.objects.filter(created_at__lt=timezone.now() - timedelta(seconds=retention)).delete()


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")
    form = SecureAuthenticationForm(request, data=request.POST or None)
    username = (request.POST.get("username") or "").strip().lower()
    ip_address = client_ip(request)
    if request.method == "POST":
        _prune_login_attempts()
        if _locked(username, ip_address):
            record_audit(
                "login_failure",
                request=request,
                target_type="user",
                target_identifier=username,
                details={"reason": "rate_limited"},
            )
            form.add_error(None, "Too many failed attempts. Try again later.")
        elif form.is_valid():
            user = form.get_user()
            login(request, user)
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            _attempts(username, ip_address).filter(succeeded=False).delete()
            LoginAttempt.objects.create(username_normalized=username, ip_address=ip_address, succeeded=True)
            record_audit(
                "login_success",
                request=request,
                actor=user,
                target_type="user",
                target_identifier=user.username,
            )
            next_url = request.GET.get("next", "")
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                return redirect(next_url)
            return redirect("dashboard:index")
        else:
            LoginAttempt.objects.create(username_normalized=username, ip_address=ip_address, succeeded=False)
            record_audit(
                "login_failure",
                request=request,
                target_type="user",
                target_identifier=username,
                details={"reason": "invalid_credentials"},
            )
    return render(request, "accounts/login.html", {"form": form})


@login_required
@require_POST
def logout_view(request):
    username = request.user.username
    record_audit("logout", request=request, target_type="user", target_identifier=username)
    logout(request)
    return redirect("accounts:login")


@login_required
def user_list(request):
    require_admin(request.user)
    query = request.GET.get("q", "").strip()
    users = (
        get_user_model()
        .objects.select_related("vibmail_access_policy")
        .annotate(mailbox_count=Count("mailbox_memberships", distinct=True))
    )
    if query:
        users = users.filter(username__icontains=query)
    page_obj = Paginator(users.order_by("username"), 25).get_page(request.GET.get("page"))
    return render(request, "accounts/user_list.html", {"page_obj": page_obj, "query": query})


def _save_user_configuration(
    *, user, form, actor, request, creating: bool, previous_active: bool | None = None
) -> None:
    selected_mailboxes = list(form.cleaned_data["assigned_mailboxes"])
    with transaction.atomic():
        policy, _created = UserAccessPolicy.objects.select_for_update().get_or_create(user=user)
        old_delete_messages = policy.can_delete_messages
        old_delete_mailboxes = policy.can_delete_mailboxes
        old_memberships = {
            membership.mailbox_id: membership.mailbox.email_address
            for membership in user.mailbox_memberships.select_related("mailbox")
        }
        policy.can_delete_messages = form.cleaned_data["can_delete_messages"]
        policy.can_delete_mailboxes = form.cleaned_data["can_delete_mailboxes"]
        policy.save(update_fields=["can_delete_messages", "can_delete_mailboxes", "updated_at"])
        new_ids = {mailbox.pk for mailbox in selected_mailboxes}
        removed = {
            mailbox_id: address
            for mailbox_id, address in old_memberships.items()
            if mailbox_id not in new_ids
        }
        added = [mailbox for mailbox in selected_mailboxes if mailbox.pk not in old_memberships]
        user.mailbox_memberships.exclude(mailbox_id__in=new_ids).delete()
        MailboxMembership.objects.bulk_create(
            [MailboxMembership(user=user, mailbox=mailbox, assigned_by=actor) for mailbox in added],
            ignore_conflicts=True,
        )
    for mailbox in added:
        record_audit(
            "mailbox_assignment_added",
            request=request,
            target_type="user",
            target_identifier=user.username,
            details={"mailbox": mailbox.email_address},
        )
    for address in removed.values():
        record_audit(
            "mailbox_assignment_removed",
            request=request,
            target_type="user",
            target_identifier=user.username,
            details={"mailbox": address},
        )
    if (old_delete_messages, old_delete_mailboxes) != (
        policy.can_delete_messages,
        policy.can_delete_mailboxes,
    ):
        record_audit(
            "user_delete_permissions_changed",
            request=request,
            target_type="user",
            target_identifier=user.username,
            details={
                "can_delete_messages": {
                    "from": old_delete_messages,
                    "to": policy.can_delete_messages,
                },
                "can_delete_mailboxes": {
                    "from": old_delete_mailboxes,
                    "to": policy.can_delete_mailboxes,
                },
            },
        )
    if previous_active is not None and previous_active != user.is_active:
        record_audit(
            "user_activated" if user.is_active else "user_deactivated",
            request=request,
            target_type="user",
            target_identifier=user.username,
        )
    record_audit(
        "user_created" if creating else "user_updated",
        request=request,
        target_type="user",
        target_identifier=user.username,
        details={
            "assigned_mailboxes": sorted(mailbox.email_address for mailbox in selected_mailboxes),
            "can_delete_messages": policy.can_delete_messages,
            "can_delete_mailboxes": policy.can_delete_mailboxes,
            "active": user.is_active,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def user_create(request):
    require_admin(request.user)
    form = UserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            _save_user_configuration(user=user, form=form, actor=request.user, request=request, creating=True)
        messages.success(request, f"User {user.username} created.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "creating": True})


@login_required
@require_http_methods(["GET", "POST"])
def user_edit(request, user_id):
    require_admin(request.user)
    user = get_object_or_404(get_user_model(), pk=user_id)
    if user.is_staff or user.is_superuser:
        messages.error(request, "Administrator accounts are not editable in this interface.")
        return redirect("accounts:user_list")
    previous_active = user.is_active
    form = UserEditForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            _save_user_configuration(
                user=user,
                form=form,
                actor=request.user,
                request=request,
                creating=False,
                previous_active=previous_active,
            )
        messages.success(request, f"User {user.username} updated.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "managed_user": user})


@login_required
@require_http_methods(["GET", "POST"])
def user_delete(request, user_id):
    require_admin(request.user)
    user = get_object_or_404(get_user_model(), pk=user_id)
    if user.pk == request.user.pk:
        messages.error(request, "You cannot delete your current administrator account.")
        return redirect("accounts:user_list")
    if user.is_staff or user.is_superuser:
        active_admins = get_user_model().objects.filter(
            is_active=True, is_staff=True
        ).union(get_user_model().objects.filter(is_active=True, is_superuser=True))
        if active_admins.count() <= 1:
            messages.error(request, "The last active administrator cannot be deleted.")
            return redirect("accounts:user_list")
        messages.error(request, "Administrator accounts are not deletable in this interface.")
        return redirect("accounts:user_list")
    if request.method == "POST":
        username = user.username
        record_audit(
            "user_deleted",
            request=request,
            target_type="user",
            target_identifier=username,
            details={"mailboxes_preserved": True},
        )
        user.delete()
        messages.success(request, f"User {username} deleted. Mailboxes and messages were preserved.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_confirm_delete.html", {"managed_user": user})
