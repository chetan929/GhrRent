from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Tenant,
    Payment,
    ReminderLog,
    Notification,
    MaintenanceComplaint,
    UserProfile,
)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "rent", "pending", "due_day", "paid"]
    search_fields = ["name", "email", "property"]
    list_filter = ["paid", "due_day"]
    fieldsets = (
        ("Tenant Information", {"fields": ("name", "email", "property", "phone")}),
        (
            "Financial Information",
            {"fields": ("rent", "pending", "due_day", "paid", "paid_month")},
        ),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["tenant", "amount", "method", "date", "note"]
    list_filter = ["method", "date"]
    search_fields = ["tenant__name", "note"]
    readonly_fields = ["date"]
    fieldsets = (
        ("Payment Details", {"fields": ("tenant", "amount", "method", "note")}),
        ("Date", {"fields": ("date",)}),
    )


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ["tenant", "status", "date"]
    list_filter = ["status", "date"]
    search_fields = ["tenant__name"]
    readonly_fields = ["date"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "is_read", "created_at"]
    list_filter = ["category", "is_read", "created_at"]
    search_fields = ["title", "message"]
    readonly_fields = ["created_at"]


@admin.register(MaintenanceComplaint)
class MaintenanceComplaintAdmin(admin.ModelAdmin):
    list_display = ["title", "tenant", "status", "priority", "created_at"]
    list_filter = ["status", "priority", "created_at"]
    search_fields = ["title", "description", "tenant__name"]
    readonly_fields = ["created_at"]
    fieldsets = (
        (
            "Complaint Details",
            {"fields": ("title", "description", "tenant", "priority", "status")},
        ),
        ("Date", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone", "organization", "created_at"]
    search_fields = ["user__username", "user__email", "phone", "organization"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("User", {"fields": ("user",)}),
        (
            "Profile Information",
            {"fields": ("phone", "organization", "bio", "profile_picture")},
        ),
        ("Dates", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


# Customize User Admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0
    fields = ["phone", "organization", "bio", "profile_picture"]


class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "date_joined",
    ]
    fieldsets = BaseUserAdmin.fieldsets + (("Additional Info", {"fields": ()}),)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Customize admin site
admin.site.site_header = "GharRent Admin"
admin.site.site_title = "GharRent Administration"
admin.site.index_title = "Property & Tenant Management"
