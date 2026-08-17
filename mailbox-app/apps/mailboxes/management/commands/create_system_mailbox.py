from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.mailboxes.mailserver import integration_enabled, mailserver_mailbox_exists
from apps.mailboxes.models import Mailbox
from apps.mailboxes.services import ProvisioningError, mailbox_paths, provision_mailbox
from apps.mailboxes.validators import validate_local_part


class Command(BaseCommand):
    help = "Create an administrator-approved reserved system mailbox such as postmaster or abuse."

    def add_arguments(self, parser):
        parser.add_argument("local_part")
        parser.add_argument("--confirm", action="store_true")
        parser.add_argument(
            "--if-missing",
            action="store_true",
            help="Preserve an existing valid system mailbox instead of treating it as a duplicate.",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError("Use --confirm after reviewing the requested system address")

        normalized = validate_local_part(options["local_part"], allow_reserved=True)
        email = f"{normalized}@{settings.MAIL_DOMAIN}"
        if options["if_missing"]:
            existing = Mailbox.objects.filter(local_part__iexact=normalized).first()
            server_exists = mailserver_mailbox_exists(email) if integration_enabled() else False
            if existing is not None:
                if existing.status != Mailbox.Status.ACTIVE or existing.deleted_at is not None:
                    raise CommandError(f"Existing system mailbox {email} is not active")
                if existing.email_address.lower() != email or existing.maildir_relative_path != (
                    f"{settings.MAIL_DOMAIN}/{normalized}/Maildir/"
                ):
                    raise CommandError(f"Existing system mailbox {email} has inconsistent metadata")
                if integration_enabled() and not server_exists:
                    raise CommandError(f"Existing system mailbox {email} is missing from the mail server")
                _root, maildir, _relative = mailbox_paths(normalized, allow_reserved=True)
                required = (maildir, maildir / "new", maildir / "cur", maildir / "tmp")
                if any(not path.is_dir() or path.is_symlink() for path in required):
                    raise CommandError(f"Existing system mailbox {email} has incomplete mail storage")
                self.stdout.write(self.style.SUCCESS(f"System mailbox {email} already exists; preserved"))
                self.stdout.write("SYSTEM_MAILBOX_STATUS=preserved")
                return
            if server_exists:
                raise CommandError(
                    f"Mail-server mailbox {email} exists without an application mailbox; "
                    "review the partial installation before repair"
                )

        try:
            mailbox = provision_mailbox(normalized, allow_reserved=True)
        except ProvisioningError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Created {mailbox.email_address}"))
        self.stdout.write("SYSTEM_MAILBOX_STATUS=created")
