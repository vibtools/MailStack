from django.urls import path

from . import views

app_name = "mailboxes"
urlpatterns = [
    path("", views.mailbox_list, name="list"),
    path("create/", views.mailbox_create, name="create"),
    path("domains/", views.domain_list, name="domains"),
    path("domains/create/", views.domain_create, name="domain_create"),
    path("domains/dns-preview/", views.domain_dns_preview, name="domain_dns_preview"),
    path("domains/<uuid:domain_uuid>/dns-status/", views.domain_dns_status, name="domain_dns_status"),
    path("domains/<uuid:domain_uuid>/default/", views.domain_make_default, name="domain_make_default"),
    path("domains/<uuid:domain_uuid>/edit/", views.domain_edit, name="domain_edit"),
    path("domains/<uuid:domain_uuid>/check/", views.domain_check, name="domain_check"),
    path("domains/<uuid:domain_uuid>/toggle/", views.domain_toggle, name="domain_toggle"),
    path("domains/<uuid:domain_uuid>/delete/", views.domain_delete, name="domain_delete"),
    path("<uuid:mailbox_uuid>/status/", views.mailbox_toggle, name="toggle"),
    path("<uuid:mailbox_uuid>/delete/", views.mailbox_delete, name="delete"),
]
