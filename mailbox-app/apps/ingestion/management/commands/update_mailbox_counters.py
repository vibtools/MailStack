from django.core.management.base import BaseCommand

from apps.ingestion.service import update_mailbox_counters
from apps.mailboxes.models import Mailbox


class Command(BaseCommand):
    help = "Recalculate mailbox message and unread counters."

    def handle(self, *args, **options):
        count = 0
        for mailbox in Mailbox.objects.iterator():
            update_mailbox_counters(mailbox)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Updated {count} mailbox counters"))
