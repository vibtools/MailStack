from django.contrib import admin

from .models import Attachment, Message

admin.site.register(Message)
admin.site.register(Attachment)
