from django.core.management.base import BaseCommand, CommandError

from apps.mailboxes.models import Mailbox
from apps.mailboxes.services import ensure_maildir


class Command(BaseCommand):
    help = "Ensure Maildir/new, cur, and tmp exist for application mailboxes."

    def add_arguments(self, parser):
        parser.add_argument("--mailbox")

    def handle(self, *args, **options):
        query = Mailbox.objects.all()
        if options["mailbox"]:
            query = query.filter(local_part__iexact=options["mailbox"])
            if not query.exists():
                raise CommandError("Mailbox not found")
        count = 0
        for mailbox in query:
            ensure_maildir(mailbox)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Verified {count} Maildir trees"))
