from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Safely rebuild missing Maildir index entries. Existing indexed messages are preserved."

    def add_arguments(self, parser):
        parser.add_argument("--mailbox")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        arguments = ["--once", "--rebuild-missing"]
        if options["mailbox"]:
            arguments.extend(["--mailbox", options["mailbox"]])
        if options["dry_run"]:
            arguments.append("--dry-run")
        call_command("ingest_maildir", *arguments)
