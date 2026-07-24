from django.contrib import admin

from .models import LoginAttempt, UserAccessPolicy

admin.site.register(LoginAttempt)
admin.site.register(UserAccessPolicy)
