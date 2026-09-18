from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import DatabaseError, transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.audit.services import record_audit
from apps.core.access import (
    accessible_mailboxes,
    is_admin,
    require_admin,
    user_can_delete_mailbox,
)

from .dns import build_dns_records, verify_dns_records, verify_domain
from .forms import DomainForm, MailboxCreateForm
from .mailserver import (
    MailServerContractError,
    delete_mailserver_domain,
    ensure_mailserver_domain,
    set_mailserver_domain_active,
)
from .models import Domain, Mailbox
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
    if request.method == "GET":
        form = MailboxCreateForm(user=request.user)
        return render(request, "mailboxes/create.html", {"form": form, "is_admin": is_admin(request.user)})
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
                domain=form.cleaned_data["domain"],
                actor=request.user,
                request=request,
                assigned_users=assigned_users,
            )
        except ProvisioningError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, f"Mailbox {mailbox.email_address} created.")
            return redirect("mailboxes:list")
    return render(
        request,
        "mailboxes/list.html",
        {
            "form": form,
            "mailbox_create_form": form,
            "open_create_modal": True,
            "page_obj": Paginator(accessible_mailboxes(request.user), 25).get_page(None),
            "query": "",
            "status": "",
            "is_admin": is_admin(request.user),
        },
    )


@login_required
def domain_list(request):
    require_admin(request.user)
    query = request.GET.get("q", "").strip()
    domains = Domain.objects.annotate(mailbox_count=Count("mailboxes")).order_by("name")
    if query:
        domains = domains.filter(Q(name__icontains=query) | Q(status__icontains=query) | Q(verification_status__icontains=query))
    return render(request, "mailboxes/domains.html", {"domains": domains, "domain_query": query})


@login_required
@require_GET
def domain_dns_status(request, domain_uuid):
    require_admin(request.user)
    domain = get_object_or_404(Domain, uuid=domain_uuid)
    result = verify_dns_records(domain.name)
    return JsonResponse(result)


@login_required
@require_POST
def domain_make_default(request, domain_uuid):
    require_admin(request.user)
    domain = get_object_or_404(Domain, uuid=domain_uuid)
    if domain.status != Domain.Status.ACTIVE or domain.verification_status != Domain.VerificationStatus.VERIFIED:
        messages.error(request, "Only an active, DNS-verified domain can be made default.")
        return redirect("mailboxes:domains")
    with transaction.atomic():
        Domain.objects.filter(is_default=True).update(is_default=False)
        domain.is_default = True
        domain.save(update_fields=["is_default", "updated_at"])
    messages.success(request, f"{domain.name} is now the default domain.")
    return redirect("mailboxes:domains")


@login_required
@require_GET
def domain_dns_preview(request):
    require_admin(request.user)
    from .validators import validate_domain

    try:
        domain = validate_domain(request.GET.get("domain", ""))
    except ValidationError:
        return JsonResponse({"error": "Enter a valid domain name before getting DNS records."}, status=400)
    return JsonResponse({"records": build_dns_records(domain)})


@login_required
@require_http_methods(["GET", "POST"])
def domain_create(request):
    require_admin(request.user)
    form = DomainForm(request.POST or None)
    if request.method == "POST" and not request.POST.get("dns_confirmed"):
        form.add_error(None, "Confirm that all DNS records have been added before saving the domain.")
    if request.method == "POST" and form.is_valid():
        domain = form.save(commit=False)
        created_external = False
        try:
            with transaction.atomic():
                created_external = ensure_mailserver_domain(
                    domain_name=domain.name,
                    active=(
                        domain.status == Domain.Status.ACTIVE
                        and domain.verification_status == Domain.VerificationStatus.VERIFIED
                    ),
                )
                domain.save()
        except Exception:
            if created_external:
                delete_mailserver_domain(domain_name=domain.name)
            form.add_error(None, "The domain could not be reconciled with the mail server.")
        else:
            messages.success(
                request, f"Domain {domain.name} added. DNS records are ready to publish."
            )
            return redirect("mailboxes:domain_edit", domain_uuid=domain.uuid)
    return render(
        request,
        "mailboxes/domain_form.html",
        {
            "form": form,
            "creating": True,
            "dns_records": [],
            "dns_preview_url": reverse("mailboxes:domain_dns_preview"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def domain_edit(request, domain_uuid):
    require_admin(request.user)
    domain = get_object_or_404(Domain, uuid=domain_uuid)
    form = DomainForm(request.POST or None, instance=domain)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                domain.status = form.cleaned_data["status"]
                domain.save(update_fields=["status", "updated_at"])
                ensure_mailserver_domain(
                    domain_name=domain.name,
                    active=(
                        domain.status == Domain.Status.ACTIVE
                        and domain.verification_status == Domain.VerificationStatus.VERIFIED
                    ),
                )
        except (DatabaseError, MailServerContractError):
            form.add_error(None, "The domain could not be reconciled with the mail server.")
        else:
            messages.success(request, f"Domain {domain.name} updated.")
            return redirect("mailboxes:domains")
    return render(
        request,
        "mailboxes/domain_form.html",
        {
            "form": form,
            "domain": domain,
            "creating": False,
            "dns_records": [],
            "dns_preview_url": reverse("mailboxes:domain_dns_preview"),
        },
    )


@login_required
@require_POST
def domain_check(request, domain_uuid):
    require_admin(request.user)
    domain = get_object_or_404(Domain, uuid=domain_uuid)
    result = verify_domain(domain.name)
    if not result["verified"]:
        try:
            set_mailserver_domain_active(domain_name=domain.name, active=False)
        except (DatabaseError, MailServerContractError):
            messages.error(request, "DNS verification failed and delivery could not be disabled safely.")
        domain.status = Domain.Status.DISABLED
    domain.verification_status = (
        Domain.VerificationStatus.VERIFIED
        if result["verified"]
        else Domain.VerificationStatus.FAILED
    )
    domain.verification_details = {
        key: value for key, value in result.items() if key != "verified"
    }
    domain.last_checked_at = timezone.now()
    update_fields = ["verification_status", "verification_details", "last_checked_at", "updated_at"]
    if not result["verified"]:
        update_fields.append("status")
    domain.save(update_fields=update_fields)
    if result["verified"]:
        messages.success(request, str(result["message"]))
    else:
        messages.error(request, str(result["message"]))
    return redirect("mailboxes:domains")


@login_required
@require_POST
def domain_toggle(request, domain_uuid):
    require_admin(request.user)
    domain = get_object_or_404(Domain, uuid=domain_uuid)
    target = Domain.Status.DISABLED if domain.status == Domain.Status.ACTIVE else Domain.Status.ACTIVE
    if target == Domain.Status.ACTIVE and domain.verification_status != Domain.VerificationStatus.VERIFIED:
        messages.error(request, "A domain must pass DNS verification before it can be enabled.")
        return redirect("mailboxes:domains")
    set_mailserver_domain_active(domain_name=domain.name, active=target == Domain.Status.ACTIVE)
    domain.status = target
    domain.save(update_fields=["status", "updated_at"])
    status_label = dict(Domain.Status.choices).get(domain.status, domain.status)
    messages.success(request, f"Domain {domain.name} {status_label.lower()}.")
    return redirect("mailboxes:domains")


@login_required
@require_POST
def domain_delete(request, domain_uuid):
    require_admin(request.user)
    domain = get_object_or_404(Domain, uuid=domain_uuid)
    if domain.is_default or domain.name == settings.MAIL_DOMAIN.strip().lower():
        messages.error(request, "The configured default domain cannot be removed.")
        return redirect("mailboxes:domains")
    if Mailbox.objects.filter(domain=domain).exists():
        messages.error(request, "A domain with mailboxes cannot be removed; disable it instead.")
        return redirect("mailboxes:domains")
    try:
        delete_mailserver_domain(domain_name=domain.name)
        domain.delete()
    except MailServerContractError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Domain {domain.name} removed.")
    return redirect("mailboxes:domains")


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
