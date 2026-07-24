from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "actor", "target_type", "target_identifier", "ip_address")
    list_filter = ("action", "target_type")
    search_fields = ("target_identifier", "actor__username", "ip_address")
    readonly_fields = [field.name for field in AuditLog._meta.fields]
