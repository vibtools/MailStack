from __future__ import annotations

import logging
import os
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.utils import timezone
from filelock import FileLock, Timeout

from apps.audit.services import record_audit

from .mailserver import (
    MailServerContractError,
    create_mailserver_mailbox,
    delete_mailserver_mailbox,
    mailserver_mailbox_exists,
    set_mailserver_mailbox_active,
)
from .models import Domain, Mailbox, MailboxMembership
from .validators import confined_path, validate_domain, validate_local_part

logger = logging.getLogger(__name__)


class ProvisioningError(RuntimeError):
    """Raised when Maildir and database provisioning cannot complete safely."""


def default_domain() -> Domain:
    domain, _created = Domain.objects.get_or_create(
        name=settings.MAIL_DOMAIN.strip().lower(),
        defaults={
            "status": Domain.Status.ACTIVE,
            "verification_status": Domain.VerificationStatus.VERIFIED,
            "verification_details": {"source": "configured-default"},
        },
    )
    return domain


def mailbox_paths(
    local_part: str,
    *,
    domain: Domain | str | None = None,
    allow_reserved: bool = False,
) -> tuple[Path, Path, str]:
    local_part = validate_local_part(local_part, allow_reserved=allow_reserved)
    domain_name = domain.name if isinstance(domain, Domain) else domain or settings.MAIL_DOMAIN
    domain_name = validate_domain(domain_name)
    mailbox_root = confined_path(settings.MAIL_STORAGE_ROOT, domain_name, local_part)
    maildir = confined_path(settings.MAIL_STORAGE_ROOT, domain_name, local_part, "Maildir")
    relative = f"{domain_name}/{local_part}/Maildir/"
    return mailbox_root, maildir, relative


def _ensure_directory(path: Path, created_paths: list[Path], *, parents: bool = False) -> None:
    try:
        path.mkdir(parents=parents, mode=0o750, exist_ok=False)
    except FileExistsError:
        if not path.is_dir() or path.is_symlink():
            raise OSError(f"Unsafe mailbox path: {path}") from None
    else:
        created_paths.append(path)
    os.chmod(path, 0o700)


def _safe_cleanup_created_paths(created_paths: list[Path]) -> None:
    for path in reversed(created_paths):
        try:
            path.rmdir()
        except FileNotFoundError:
            continue
        except OSError:
            logger.exception(
                "Failed to remove a newly created empty Maildir path",
                extra={"event": "provision_cleanup_failed"},
            )


def _provision_mailbox_locked(
    normalized: str,
    *,
    domain: Domain,
    actor=None,
    request=None,
    allow_reserved: bool = False,
    assigned_users=None,
) -> Mailbox:
    email = f"{normalized}@{domain.name}"
    mailbox_root, maildir, relative = mailbox_paths(normalized, domain=domain, allow_reserved=allow_reserved)
    mailbox_exists = Mailbox.objects.filter(domain=domain, local_part__iexact=normalized).exists()
    if mailbox_exists or mailserver_mailbox_exists(email=email, domain_name=domain.name):
        raise ProvisioningError(f"Mailbox {email} already exists or is permanently reserved.")
    created_paths: list[Path] = []
    try:
        _ensure_directory(mailbox_root, created_paths, parents=True)
        _ensure_directory(maildir, created_paths)
        for child in ("new", "cur", "tmp"):
            _ensure_directory(maildir / child, created_paths)
    except OSError as exc:
        _safe_cleanup_created_paths(created_paths)
        logger.exception(
            "Mailbox filesystem provisioning failed",
            extra={"event": "mailbox_provision_failed", "mailbox": normalized},
        )
        record_audit(
            "mailbox_provisioning_failure",
            request=request,
            actor=actor,
            target_type="mailbox",
            target_identifier=normalized,
            details={"stage": "filesystem", "error_type": type(exc).__name__},
        )
        raise ProvisioningError("Unable to create the mailbox filesystem safely.") from exc
    remote_mailbox_created = False
    try:
        with transaction.atomic():
            mailserver_kwargs = {
                "local_part": normalized,
                "email": email,
                "maildir": relative,
                "domain_name": domain.name,
            }
            create_mailserver_mailbox(**mailserver_kwargs)
            remote_mailbox_created = True
            mailbox = Mailbox(
                domain=domain,
                local_part=normalized,
                email_address=email,
                maildir_relative_path=relative,
            )
            mailbox.full_clean()
            mailbox.save()
            users = list(assigned_users or [])
            MailboxMembership.objects.bulk_create(
                [MailboxMembership(user=user, mailbox=mailbox, assigned_by=actor) for user in users],
                ignore_conflicts=True,
            )
    except (DatabaseError, IntegrityError, ValidationError, MailServerContractError) as exc:
        if remote_mailbox_created:
            try:
                delete_mailserver_mailbox(email=email)
            except MailServerContractError:
                logger.exception(
                    "Failed to remove an orphaned mail-server mailbox",
                    extra={"event": "mailbox_remote_cleanup_failed", "mailbox": email},
                )
        _safe_cleanup_created_paths(created_paths)
        record_audit(
            "mailbox_provisioning_failure",
            request=request,
            actor=actor,
            target_type="mailbox",
            target_identifier=normalized,
            details={"stage": "database", "error_type": type(exc).__name__},
        )
        raise ProvisioningError(str(exc) or "Unable to create the mailbox database record.") from exc
    record_audit(
        "mailbox_create",
        request=request,
        actor=actor,
        target_type="mailbox",
        target_identifier=mailbox.email_address,
        details={"assigned_user_ids": [user.pk for user in users]},
    )
    logger.info(
        "Mailbox provisioned", extra={"event": "mailbox_provisioned", "mailbox": mailbox.email_address}
    )
    return mailbox


def provision_mailbox(
    local_part: str,
    *,
    domain: Domain | None = None,
    actor=None,
    request=None,
    allow_reserved: bool = False,
    assigned_users=None,
) -> Mailbox:
    normalized = validate_local_part(local_part, allow_reserved=allow_reserved)
    domain = domain or default_domain()
    if (
        domain.status != Domain.Status.ACTIVE
        or domain.verification_status != Domain.VerificationStatus.VERIFIED
    ):
        raise ProvisioningError("Mailbox provisioning requires an active, DNS-verified domain.")
    lock_root = Path(settings.MAILBOX_PROVISION_LOCK_ROOT)
    try:
        lock_root.mkdir(parents=True, mode=0o700, exist_ok=True)
        if lock_root.is_symlink() or not lock_root.is_dir():
            raise OSError("Provisioning lock root is unsafe")
        os.chmod(lock_root, 0o700)
        lock_name = (
            f"{normalized}.lock"
            if domain.name == settings.MAIL_DOMAIN.strip().lower()
            else f"{domain.name}-{normalized}.lock"
        )
        lock_path = confined_path(lock_root, lock_name)
        with FileLock(
            str(lock_path),
            timeout=settings.MAILBOX_PROVISION_LOCK_TIMEOUT_SECONDS,
        ):
            return _provision_mailbox_locked(
                normalized,
                domain=domain,
                actor=actor,
                request=request,
                allow_reserved=allow_reserved,
                assigned_users=assigned_users,
            )
    except Timeout as exc:
        record_audit(
            "mailbox_provisioning_failure",
            request=request,
            actor=actor,
            target_type="mailbox",
            target_identifier=normalized,
            details={"stage": "lock", "error_type": type(exc).__name__},
        )
        raise ProvisioningError(
            f"Mailbox {normalized}@{domain.name} is currently being provisioned."
        ) from exc
    except (OSError, ValidationError) as exc:
        record_audit(
            "mailbox_provisioning_failure",
            request=request,
            actor=actor,
            target_type="mailbox",
            target_identifier=normalized,
            details={"stage": "lock_filesystem", "error_type": type(exc).__name__},
        )
        raise ProvisioningError("Unable to acquire a safe mailbox provisioning lock.") from exc


def set_mailbox_status(mailbox: Mailbox, status: str) -> Mailbox:
    if mailbox.deleted_at is not None or mailbox.status == Mailbox.Status.DELETED:
        raise ProvisioningError("Deleted mailboxes cannot be enabled or disabled.")
    if status not in {Mailbox.Status.ACTIVE, Mailbox.Status.DISABLED}:
        raise ProvisioningError("Invalid mailbox status.")
    try:
        with transaction.atomic():
            set_mailserver_mailbox_active(
                email=mailbox.email_address,
                active=status == Mailbox.Status.ACTIVE,
            )
            mailbox.status = status
            mailbox.save(update_fields=["status", "updated_at"])
    except (DatabaseError, IntegrityError, MailServerContractError) as exc:
        raise ProvisioningError(str(exc) or "Unable to update mailbox status safely.") from exc
    return mailbox


def soft_delete_mailbox(mailbox: Mailbox, *, actor=None, request=None) -> Mailbox:
    if mailbox.deleted_at is not None or mailbox.status == Mailbox.Status.DELETED:
        return mailbox
    try:
        with transaction.atomic():
            locked = Mailbox.objects.select_for_update().get(pk=mailbox.pk)
            if locked.deleted_at is not None:
                return locked
            set_mailserver_mailbox_active(email=locked.email_address, active=False)
            locked.status = Mailbox.Status.DELETED
            locked.deleted_at = timezone.now()
            locked.deleted_by = actor if getattr(actor, "is_authenticated", False) else None
            locked.save(update_fields=["status", "deleted_at", "deleted_by", "updated_at"])
    except (DatabaseError, IntegrityError, MailServerContractError) as exc:
        raise ProvisioningError(str(exc) or "Unable to delete mailbox safely.") from exc
    record_audit(
        "mailbox_deleted",
        request=request,
        actor=actor,
        target_type="mailbox",
        target_identifier=locked.email_address,
        details={"data_preserved": True, "address_reserved": True},
    )
    return locked


def ensure_maildir(mailbox: Mailbox) -> Path:
    mailbox_root, maildir, _relative = mailbox_paths(
        mailbox.local_part, domain=mailbox.domain, allow_reserved=True
    )
    created_paths: list[Path] = []
    _ensure_directory(mailbox_root, created_paths, parents=True)
    _ensure_directory(maildir, created_paths)
    for child in ("new", "cur", "tmp"):
        _ensure_directory(maildir / child, created_paths)
    return maildir
