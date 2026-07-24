from django.contrib import admin

from .models import Mailbox, MailboxMembership


@admin.register(Mailbox)
class MailboxAdmin(admin.ModelAdmin):
    list_display = (
        "email_address",
        "status",
        "total_messages",
        "unread_messages",
        "last_received_at",
        "deleted_at",
    )
    list_filter = ("status",)
    search_fields = ("local_part", "email_address")


admin.site.register(MailboxMembership)
