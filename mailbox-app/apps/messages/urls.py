from django.urls import path

from . import views

app_name = "messages"
urlpatterns = [
    path("live/", views.live_updates, name="live_updates"),
    path("mailbox/<uuid:mailbox_uuid>/", views.inbox, name="inbox"),
    path("mailbox/<uuid:mailbox_uuid>/<uuid:message_uuid>/", views.message_detail, name="detail"),
    path("html/<uuid:message_uuid>/", views.safe_html, name="safe_html"),
    path("mailbox/<uuid:mailbox_uuid>/<uuid:message_uuid>/state/", views.mark_state, name="mark_state"),
    path("mailbox/<uuid:mailbox_uuid>/<uuid:message_uuid>/delete/", views.message_delete, name="delete"),
    path(
        "mailbox/<uuid:mailbox_uuid>/<uuid:message_uuid>/attachment/<uuid:attachment_uuid>/",
        views.attachment_download,
        name="attachment_download",
    ),
]
