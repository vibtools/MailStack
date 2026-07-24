from django.urls import include, path

handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"

urlpatterns = [
    path("", include("apps.dashboard.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("mailboxes/", include("apps.mailboxes.urls")),
    path("messages/", include("apps.messages.urls")),
    path("health/", include("apps.core.urls")),
]
