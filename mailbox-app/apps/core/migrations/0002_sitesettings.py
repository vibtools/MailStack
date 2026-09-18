from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("site_name", models.CharField(default="MailStack", max_length=120)),
                ("site_tagline", models.CharField(default="Self-hosted mail server and shared team inbox.", max_length=200)),
                ("logo", models.FileField(blank=True, upload_to="site-settings/")),
                ("favicon", models.FileField(blank=True, upload_to="site-settings/")),
                ("support_email", models.EmailField(default="", max_length=254)),
                ("contact_phone", models.CharField(blank=True, max_length=40)),
                ("office_address", models.CharField(blank=True, max_length=255)),
                ("footer_description", models.TextField(blank=True)),
                ("copyright_text", models.CharField(default="Authorized team use only.", max_length=255)),
                ("source_code_url", models.URLField(default="https://github.com/vibtools/MailStack")),
                ("privacy_url", models.CharField(default="/privacy/", max_length=500)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "site settings", "verbose_name_plural": "site settings"},
        ),
    ]
