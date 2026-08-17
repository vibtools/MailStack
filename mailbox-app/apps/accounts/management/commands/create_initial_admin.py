from __future__ import annotations

import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the initial private administrator without a default password."

    def add_arguments(self, parser):
        parser.add_argument("--username")
        parser.add_argument("--password-env")
        parser.add_argument(
            "--if-missing",
            action="store_true",
            help="Preserve an existing valid administrator with the requested username.",
        )

    def handle(self, *args, **options):
        username = options["username"] or input("Administrator username: ").strip()
        if not username:
            raise CommandError("Username is required")
        user_model = get_user_model()
        existing_users = user_model.objects.all()
        if existing_users.exists():
            if not options["if_missing"]:
                raise CommandError(
                    "An application administrator already exists; use the built-in "
                    "changepassword command for recovery"
                )
            existing = existing_users.filter(username=username).first()
            if existing is None:
                raise CommandError(
                    f"Application users already exist but administrator {username!r} is missing; "
                    "review the partial installation before repair"
                )
            if not (existing.is_active and existing.is_staff and existing.is_superuser):
                raise CommandError(
                    f"Existing user {username!r} is not an active administrator; "
                    "review the partial installation before repair"
                )
            self.stdout.write(self.style.SUCCESS(f"Administrator {username!r} already exists; preserved"))
            self.stdout.write("INITIAL_ADMIN_STATUS=preserved")
            return

        password = None
        if options["password_env"]:
            import os

            password = os.getenv(options["password_env"])
            if not password:
                raise CommandError("The requested password environment variable is missing")
        else:
            first = getpass.getpass("Password: ")
            second = getpass.getpass("Confirm password: ")
            if first != second:
                raise CommandError("Passwords do not match")
            password = first
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc
        user_model.objects.create_superuser(username=username, password=password)
        self.stdout.write(self.style.SUCCESS(f"Administrator {username!r} created"))
        self.stdout.write("INITIAL_ADMIN_STATUS=created")
