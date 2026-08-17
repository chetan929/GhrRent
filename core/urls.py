from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # Authentication
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    # User profile
    path("profile/", views.user_profile, name="user_profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("gmail/connect/", views.gmail_connect, name="gmail_connect"),
    path("gmail/callback/", views.gmail_callback, name="gmail_callback"),
    path("gmail/disconnect/", views.gmail_disconnect, name="gmail_disconnect"),
    # API Endpoints (JSON)
    path("api/tenants/add/", views.api_add_tenant, name="api_add_tenant"),
    path(
        "api/tenants/<int:tenant_id>/delete/",
        views.api_delete_tenant,
        name="api_delete_tenant",
    ),
    path("api/payments/record/", views.api_record_payment, name="api_record_payment"),
    path("api/payments/get/", views.api_get_payments, name="api_get_payments"),
    # Dashboard and tenant management
    path("", views.dashboard, name="dashboard"),
    path("add-tenant/", views.add_tenant, name="add_tenant"),
    path("record-payment/", views.record_payment, name="record_payment"),
    path("delete-tenant/<int:tenant_id>/", views.delete_tenant, name="delete_tenant"),
    # Reminders
    path("send-reminder/<int:tenant_id>/", views.send_reminder, name="send_reminder"),
    path("send-auto-reminders/", views.send_auto_reminders, name="send_auto_reminders"),
    path("send-all-reminders/", views.send_all_reminders, name="send_all_reminders"),
    path(
        "send-email-reminder/<int:tenant_id>/",
        views.send_email_reminder,
        name="send_email_reminder",
    ),
    # Notifications and complaints
    path("notifications/", views.notifications, name="notifications"),
    path(
        "add-maintenance-complaint/",
        views.add_maintenance_complaint,
        name="add_maintenance_complaint",
    ),
]
