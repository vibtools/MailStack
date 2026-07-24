from django.core.management.base import BaseCommand, CommandError

from apps.mailboxes.services import ProvisioningError, provision_mailbox


class Command(BaseCommand):
    help = "Create an administrator-approved reserved system mailbox such as postmaster or abuse."

    def add_arguments(self, parser):
        parser.add_argument("local_part")
        parser.add_argument("--confirm", action="store_true")

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError("Use --confirm after reviewing the requested system address")
        try:
            mailbox = provision_mailbox(options["local_part"], allow_reserved=True)
        except ProvisioningError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Created {mailbox.email_address}"))
