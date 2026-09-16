from django.urls import path

from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.index, name="index"),
    path("system-update/", views.system_update_page, name="system_update_page"),
    path("api/update/check/", views.check_update, name="check_update"),
    path("api/update/start/", views.start_update, name="start_update"),
    path("api/update/status/", views.update_status, name="update_status"),
]
