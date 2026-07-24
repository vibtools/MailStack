from django.urls import path

from . import views

app_name = "mailboxes"
urlpatterns = [
    path("", views.mailbox_list, name="list"),
    path("create/", views.mailbox_create, name="create"),
    path("<uuid:mailbox_uuid>/status/", views.mailbox_toggle, name="toggle"),
    path("<uuid:mailbox_uuid>/delete/", views.mailbox_delete, name="delete"),
]
