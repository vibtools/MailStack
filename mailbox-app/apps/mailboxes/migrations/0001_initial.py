# Generated for MailStack MVP 1.1.0 MariaDB-compatible deployment.

import uuid

import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Mailbox",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("local_part", models.CharField(max_length=64, unique=True)),
                ("email_address", models.EmailField(max_length=320, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("disabled", "Disabled")],
                        db_index=True,
                        default="active",
                        max_length=16,
                    ),
                ),
                ("maildir_relative_path", models.CharField(max_length=255)),
                ("total_messages", models.PositiveBigIntegerField(default=0)),
                ("unread_messages", models.PositiveBigIntegerField(default=0)),
                ("last_received_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["local_part"],
                "indexes": [
                    models.Index(fields=["status", "created_at"], name="mailboxes_m_status_434952_idx")
                ],
                "constraints": [
                    models.UniqueConstraint(
                        django.db.models.functions.text.Lower("local_part"),
                        name="mailbox_local_part_ci_unique",
                    ),
                    models.UniqueConstraint(
                        django.db.models.functions.text.Lower("email_address"),
                        name="mailbox_email_address_ci_unique",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("status__in", ["active", "disabled"])),
                        name="mailbox_valid_status",
                    ),
                ],
            },
        ),
    ]
