from django.core.management.base import BaseCommand, CommandError

from apps.mailboxes.mailserver import MailServerContractError, verify_mailserver_schema


class Command(BaseCommand):
    help = "Verify the existing MariaDB mail-server schema and Postfix view are accessible."

    def handle(self, *args, **options):
        try:
            result = verify_mailserver_schema()
        except MailServerContractError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                "Mail-server schema verified "
                f"(domains={result['domains']}, mailboxes={result['mailboxes']}, "
                f"postfix_rows={result['postfix_rows']})"
            )
        )
