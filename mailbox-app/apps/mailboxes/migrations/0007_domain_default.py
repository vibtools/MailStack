from django.conf import settings
from django.db import migrations, models


def mark_configured_default(apps, schema_editor):
    Domain = apps.get_model("mailboxes", "Domain")
    Domain.objects.filter(name=settings.MAIL_DOMAIN.strip().lower()).update(is_default=True)


class Migration(migrations.Migration):
    dependencies = [("mailboxes", "0006_restore_domain_aware_postfix_view")]

    operations = [
        migrations.AddField(
            model_name="domain",
            name="is_default",
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.RunPython(mark_configured_default, migrations.RunPython.noop),
    ]
