from django.conf import settings

from .access import is_admin


def application_context(request):
    user = getattr(request, "user", None)
    return {
        "app_name": "MailStack",
        "mail_domain": settings.MAIL_DOMAIN,
        "app_hostname": settings.APP_HOSTNAME,
        "source_code_url": settings.SOURCE_CODE_URL,
        "company_url": settings.COMPANY_URL,
        "open_source_hub_url": settings.OPEN_SOURCE_HUB_URL,
        "subdomain_service_url": settings.SUBDOMAIN_SERVICE_URL,
        "is_vibmail_admin": is_admin(user),
    }
