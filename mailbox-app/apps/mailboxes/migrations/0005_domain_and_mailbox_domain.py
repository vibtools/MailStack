from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.text
import uuid


def drop_view(_apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        schema_editor.execute("DROP VIEW IF EXISTS postfix_virtual_mailboxes")


def restore_view(_apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        schema_editor.execute(
            "CREATE VIEW postfix_virtual_mailboxes AS SELECT lower(email_address) AS email, "
            "maildir_relative_path AS maildir_path FROM mailboxes_mailbox WHERE status = 'active' "
            "AND deleted_at IS NULL"
        )


def backfill_default_domain(apps, schema_editor):
    Domain = apps.get_model("mailboxes", "Domain")
    Mailbox = apps.get_model("mailboxes", "Mailbox")
    name = settings.MAIL_DOMAIN.strip().lower()
    domain, _created = Domain.objects.get_or_create(
        name=name,
        defaults={"status": "active", "verification_status": "verified", "verification_details": {"source": "migration"}},
    )
    Mailbox.objects.filter(domain__isnull=True).update(domain=domain)


class Migration(migrations.Migration):
    dependencies = [("mailboxes", "0004_generic_postfix_virtual_mailboxes_view")]
    operations = [
        migrations.RunPython(drop_view, reverse_code=restore_view),
        migrations.CreateModel(
            name="Domain",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(max_length=253, unique=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("disabled", "Disabled")], db_index=True, default="active", max_length=16)),
                ("verification_status", models.CharField(choices=[("pending", "Pending"), ("verified", "Verified"), ("failed", "Failed")], db_index=True, default="pending", max_length=16)),
                ("last_checked_at", models.DateTimeField(blank=True, null=True)),
                ("verification_details", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddConstraint(
            model_name="domain",
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower("name"), name="mail_domain_name_ci_unique"),
        ),
        migrations.AddConstraint(
            model_name="domain",
            constraint=models.CheckConstraint(condition=models.Q(status__in=["active", "disabled"]), name="mail_domain_valid_status"),
        ),
        migrations.AddConstraint(
            model_name="domain",
            constraint=models.CheckConstraint(condition=models.Q(verification_status__in=["pending", "verified", "failed"]), name="mail_domain_valid_verification_status"),
        ),
        migrations.AddField(
            model_name="mailbox",
            name="domain",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="mailboxes", to="mailboxes.domain"),
        ),
        migrations.RunPython(backfill_default_domain, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="mailbox",
            name="domain",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="mailboxes", to="mailboxes.domain"),
        ),
        migrations.AlterField(model_name="mailbox", name="local_part", field=models.CharField(max_length=64)),
        migrations.RemoveConstraint(model_name="mailbox", name="mailbox_local_part_ci_unique"),
        migrations.AddConstraint(
            model_name="mailbox",
            constraint=models.UniqueConstraint("domain", django.db.models.functions.text.Lower("local_part"), name="mailbox_domain_local_part_ci_unique"),
        ),
        migrations.RunPython(restore_view, reverse_code=drop_view),
    ]
