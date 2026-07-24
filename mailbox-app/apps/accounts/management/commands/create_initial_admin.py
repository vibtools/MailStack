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

    def handle(self, *args, **options):
        username = options["username"] or input("Administrator username: ").strip()
        if not username:
            raise CommandError("Username is required")
        user_model = get_user_model()
        if user_model.objects.exists():
            raise CommandError(
                "An application administrator already exists; use the built-in "
                "changepassword command for recovery"
            )
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
