from django.contrib import admin

from .models import Domain, Mailbox, MailboxMembership


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "verification_status", "created_at", "updated_at")
    list_filter = ("status", "verification_status")
    search_fields = ("name",)
    readonly_fields = ("uuid", "created_at", "updated_at")


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
