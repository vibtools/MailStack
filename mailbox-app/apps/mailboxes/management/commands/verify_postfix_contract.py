from django.core.management.base import BaseCommand, CommandError

from apps.mailboxes.mailserver import postfix_rows
from apps.mailboxes.models import Mailbox


class Command(BaseCommand):
    help = "Verify the existing Postfix MariaDB view matches active application mailboxes."

    def handle(self, *args, **options):
        try:
            rows = postfix_rows()
        except Exception as exc:
            raise CommandError("Postfix lookup view is unavailable") from exc
        expected = list(
            Mailbox.objects.filter(status=Mailbox.Status.ACTIVE)
            .order_by("email_address")
            .values_list("email_address", "maildir_relative_path")
        )
        if rows != expected:
            raise CommandError(f"Postfix lookup view mismatch: expected {expected!r}, got {rows!r}")
        self.stdout.write(
            self.style.SUCCESS(f"Postfix lookup contract verified ({len(rows)} active mailboxes)")
        )
