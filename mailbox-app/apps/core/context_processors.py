from django.conf import settings

from .access import is_admin


def application_context(request):
    user = getattr(request, "user", None)
    mailbox_create_form = None
    if getattr(user, "is_authenticated", False):
        from apps.mailboxes.forms import MailboxCreateForm

        mailbox_create_form = MailboxCreateForm(user=user)
    return {
        "app_name": "MailStack",
        "mail_domain": settings.MAIL_DOMAIN,
        "mail_hostname": settings.MAIL_HOSTNAME,
        "app_hostname": settings.APP_HOSTNAME,
        "source_code_url": settings.SOURCE_CODE_URL,
        "company_url": settings.COMPANY_URL,
        "open_source_hub_url": settings.OPEN_SOURCE_HUB_URL,
        "subdomain_service_url": settings.SUBDOMAIN_SERVICE_URL,
        "is_vibmail_admin": is_admin(user),
        "mailbox_create_form": mailbox_create_form,
    }
