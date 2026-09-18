from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0002_sitesettings")]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="privacy_url",
            field=models.CharField(default="/privacy/", max_length=500),
        ),
    ]
