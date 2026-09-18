from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
	path("live/", views.live, name="live"),
	path("ready/", views.ready, name="ready"),
	path("site-settings/", views.site_settings_api, name="site_settings_api"),
]
