from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.mailboxes.mailserver import (
    MailServerContractError,
    ensure_mailserver_domain,
    list_mailserver_mailboxes,
)
from apps.mailboxes.models import Domain, Mailbox
from apps.mailboxes.validators import validate_domain, validate_local_part


class Command(BaseCommand):
    help = "Import or reconcile mail-server MariaDB mailbox rows into the Django application database."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--strict", action="store_true")

    def handle(self, *args, **options):
        try:
            source_rows = list_mailserver_mailboxes()
        except MailServerContractError as exc:
            raise CommandError(str(exc)) from exc
        created = 0
        updated = 0
        unchanged = 0
        errors: list[str] = []
        with transaction.atomic():
            for source in source_rows:
                try:
                    local_part = validate_local_part(source.local_part, allow_reserved=True)
                    domain_name = validate_domain(source.email.rsplit("@", 1)[-1])
                    domain, _created = Domain.objects.get_or_create(
                        name=domain_name,
                        defaults={
                            "status": Domain.Status.DISABLED,
                            "verification_status": Domain.VerificationStatus.PENDING,
                            "verification_details": {"source": "mailserver-sync"},
                        },
                    )
                    domain_ready = (
                        domain.status == Domain.Status.ACTIVE
                        and domain.verification_status == Domain.VerificationStatus.VERIFIED
                    )
                    ensure_mailserver_domain(domain_name=domain.name, active=domain_ready)
                    status = (
                        Mailbox.Status.ACTIVE
                        if source.active and domain_ready
                        else Mailbox.Status.DISABLED
                    )
                    expected_email = f"{local_part}@{domain.name}"
                    expected_maildir = f"{domain.name}/{local_part}/Maildir/"
                    if source.email.lower() != expected_email or source.maildir != expected_maildir:
                        raise ValueError("email or Maildir path violates the MailStack contract")
                    mailbox = Mailbox.objects.filter(domain=domain, local_part__iexact=local_part).first()
                    if mailbox is None:
                        if not options["dry_run"]:
                            Mailbox.objects.create(
                                domain=domain,
                                local_part=local_part,
                                email_address=expected_email,
                                maildir_relative_path=expected_maildir,
                                status=status,
                            )
                        created += 1
                        continue
                    changes = []
                    for field, value in (
                        ("email_address", expected_email),
                        ("maildir_relative_path", expected_maildir),
                        ("status", status),
                    ):
                        if getattr(mailbox, field) != value:
                            setattr(mailbox, field, value)
                            changes.append(field)
                    if changes:
                        if not options["dry_run"]:
                            mailbox.full_clean()
                            mailbox.save(update_fields=[*changes, "updated_at"])
                        updated += 1
                    else:
                        unchanged += 1
                except Exception as exc:  # one malformed source row must be reported precisely
                    errors.append(f"{source.email}: {exc}")
            if options["dry_run"]:
                transaction.set_rollback(True)
        self.stdout.write(
            "Mail-server sync: "
            f"created={created}, updated={updated}, unchanged={unchanged}, errors={len(errors)}"
        )
        for error in errors:
            self.stderr.write(error)
        if errors and options["strict"]:
            raise CommandError("Mail-server synchronization found invalid source rows")
