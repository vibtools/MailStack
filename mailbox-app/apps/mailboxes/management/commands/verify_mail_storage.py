from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.mailboxes.models import Mailbox
from apps.mailboxes.services import mailbox_paths


class Command(BaseCommand):
    help = "Verify configured mail storage and every indexed Maildir."

    def handle(self, *args, **options):
        root = Path(settings.MAIL_STORAGE_ROOT)
        if not root.is_dir():
            raise CommandError("Mail storage root is missing or not a directory")
        errors = []
        for mailbox in Mailbox.objects.iterator():
            _mailbox_root, maildir, _relative = mailbox_paths(mailbox.local_part, allow_reserved=True)
            for child in (maildir / "new", maildir / "cur", maildir / "tmp"):
                if not child.is_dir():
                    errors.append(f"{mailbox.email_address}: missing {child.name}")
        if errors:
            raise CommandError("; ".join(errors))
        self.stdout.write(self.style.SUCCESS("Mail storage contract verified"))
