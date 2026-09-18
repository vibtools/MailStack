from django.conf import settings

from .access import is_admin
from .models import SiteSettings


def application_context(request):
    user = getattr(request, "user", None)
    mailbox_create_form = None
    mail_domain = settings.MAIL_DOMAIN
    if getattr(user, "is_authenticated", False):
        from apps.mailboxes.forms import MailboxCreateForm
        from apps.mailboxes.services import default_domain

        mailbox_create_form = MailboxCreateForm(user=user)
        mail_domain = default_domain().name
    site_settings = SiteSettings.get_solo()
    return {
        "app_name": site_settings.site_name,
        "site_tagline": site_settings.site_tagline,
        "site_settings": site_settings,
        "mail_domain": mail_domain,
        "mail_hostname": settings.MAIL_HOSTNAME,
        "server_ip": settings.SERVER_IP,
        "app_hostname": settings.APP_HOSTNAME,
        "source_code_url": site_settings.source_code_url or settings.SOURCE_CODE_URL,
        "company_url": settings.COMPANY_URL,
        "open_source_hub_url": settings.OPEN_SOURCE_HUB_URL,
        "subdomain_service_url": settings.SUBDOMAIN_SERVICE_URL,
        "is_vibmail_admin": is_admin(user),
        "mailbox_create_form": mailbox_create_form,
    }
