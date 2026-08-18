import base64
import json
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse

from core.email_service import EmailReminderService
from core.forms import TenantForm
from core.models import (
    GmailCredential,
    MaintenanceComplaint,
    Notification,
    Tenant,
    UserProfile,
)


class FreeReminderAndComplaintTests(TestCase):
    def test_build_reminder_email_contains_subject_and_amounts(self):
        email = EmailReminderService.build_reminder_email(
            tenant_name="Rahul",
            tenant_email="rahul@example.com",
            rent_amount=6000,
            pending_amount=2000,
        )

        self.assertIn("Rahul", email["subject"])
        self.assertIn("₹6,000", email["body"])
        self.assertIn("₹2,000", email["body"])
        self.assertIn("₹8,000", email["body"])
        self.assertEqual(email["to"], ["rahul@example.com"])

    def test_maintenance_complaint_defaults_and_notification_model(self):
        complaint = MaintenanceComplaint.objects.create(
            title="Water leakage",
            description="Kitchen pipe leaking",
            priority="Medium",
        )

        self.assertEqual(complaint.status, "Open")
        self.assertEqual(complaint.priority, "Medium")

        notification = Notification.objects.create(
            title="Complaint registered",
            message="Water leakage complaint received.",
            category="maintenance",
        )

        self.assertFalse(notification.is_read)
        self.assertEqual(notification.category, "maintenance")

    def test_reminder_email_includes_due_date_and_hindi_language(self):
        email = EmailReminderService.build_reminder_email(
            tenant_name="Rahul",
            tenant_email="rahul@example.com",
            rent_amount=6000,
            pending_amount=2000,
            due_date="2026-08-25",
            language="hindi",
        )

        self.assertIn("25 Aug 2026", email["body"])
        self.assertIn("नियत तिथि", email["body"])
        self.assertIn("कुल देय राशि", email["body"])

    def test_add_tenant_api_requires_login(self):
        response = self.client.post(
            reverse("core:api_add_tenant"),
            data=json.dumps(
                {"name": "Test", "email": "test@test.com", "rent": 5000, "due_day": 10}
            ),
            content_type="application/json",
        )
        # Should redirect to login (302) or return 403 Forbidden
        self.assertIn(response.status_code, [302, 403])

    def test_add_tenant_api_success(self):
        user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("core:api_add_tenant"),
            data=json.dumps(
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "rent": 5000,
                    "due_day": 10,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("Tenant added successfully", data["message"])
        self.assertTrue(Tenant.objects.filter(name="John Doe").exists())

    def test_add_tenant_api_requires_name(self):
        user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("core:api_add_tenant"),
            data=json.dumps(
                {
                    "name": "",
                    "email": "john@example.com",
                    "rent": 5000,
                    "due_day": 10,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("Name is required", data["message"])

    def test_add_tenant_without_phone_succeeds(self):
        user = get_user_model().objects.create_user(
            username="tenantadmin2",
            email="admin2@example.com",
            password="pass123",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("core:api_add_tenant"),
            data=json.dumps(
                {
                    "name": "Alice Tenant",
                    "email": "alice@example.com",
                    "phone": "",
                    "rent": 5000,
                    "pending": 1000,
                    "due_day": 10,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Tenant.objects.filter(name="Alice Tenant").exists())

    def test_delete_tenant_api_removes_record(self):
        user = get_user_model().objects.create_user(
            username="tenantadmin",
            email="admin@example.com",
            password="pass123",
        )
        self.client.force_login(user)

        tenant = Tenant.objects.create(
            user=user,
            name="Alice Tenant",
            phone="9876543210",
            rent=5000,
            pending=1000,
            due_day=10,
        )

        response = self.client.delete(
            reverse("core:api_delete_tenant", args=[tenant.id]),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tenant.objects.filter(id=tenant.id).exists())

    def test_tenant_form_rejects_negative_and_too_large_rent(self):
        form = {
            "name": "Bad Rent Tenant",
            "email": "bad@example.com",
            "rent": "-1",
            "pending": "0",
            "due_day": 10,
        }
        tenant_form = TenantForm(data=form)
        self.assertFalse(tenant_form.is_valid())
        self.assertIn("rent", tenant_form.errors)

        form["rent"] = "1000000000"
        tenant_form = TenantForm(data=form)
        self.assertFalse(tenant_form.is_valid())
        self.assertIn("rent", tenant_form.errors)

    def test_dashboard_handles_invalid_legacy_tenant_record(self):
        user = get_user_model().objects.create_user(
            username="legacybadtenant",
            email="legacy@example.com",
            password="pass123",
        )
        self.client.force_login(user)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO core_tenant (user_id, name, email, phone, property, rent, pending, due_day, paid, paid_month)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    user.id,
                    "Legacy bad tenant",
                    "legacy@example.com",
                    "",
                    "",
                    "1000000000",
                    "0",
                    5,
                    False,
                    None,
                ],
            )

        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 200)

    def test_dashboard_handles_missing_user_profile(self):
        user = get_user_model().objects.create_user(
            username="profileless",
            email="profileless@example.com",
            password="pass123",
        )
        UserProfile.objects.filter(user=user).delete()
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_register_new_user_then_login_succeeds(self):
        username = "brandnewuser_20260815"
        email = "brandnewuser_20260815@example.com"
        password = "securepass123"

        response = self.client.post(
            reverse("core:register"),
            {
                "username": username,
                "email": email,
                "password": password,
                "password_confirm": password,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username=username).exists())
        user = get_user_model().objects.get(username=username)
        self.assertEqual(user.email.lower(), email.lower())
        self.assertTrue(user.check_password(password))

        self.client.logout()
        login_response = self.client.post(
            reverse("core:login"),
            {"username": username, "password": password},
            follow=True,
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.wsgi_request.user.is_authenticated)
        self.assertRedirects(login_response, reverse("core:dashboard"))

    @override_settings(
        GOOGLE_CLIENT_ID="test-client-id",
        GOOGLE_CLIENT_SECRET="test-client-secret",
        EMAIL_HOST_USER="",
        EMAIL_HOST_PASSWORD="",
    )
    @patch("core.email_service.build")
    def test_send_email_reminder_uses_connected_gmail_for_user(self, mock_build):
        user = get_user_model().objects.create_user(
            username="gmailuser",
            email="gmailuser@example.com",
            password="pass123",
        )
        GmailCredential.objects.create(
            user=user,
            gmail_email="user@gmail.com",
            access_token="token-123",
            refresh_token="refresh-123",
        )

        mock_service = Mock()
        mock_messages = Mock()
        mock_messages.send.return_value.execute.return_value = {"id": "abc123"}
        mock_service.users.return_value.messages.return_value = mock_messages
        mock_build.return_value = mock_service

        result = EmailReminderService.send_email_reminder(
            tenant_name="Sam",
            tenant_email="sam@example.com",
            rent_amount=5000,
            pending_amount=1000,
            language="english",
            user=user,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "Sent")
        mock_build.assert_called_once()
        mock_messages.send.assert_called_once()

        sent_payload = mock_messages.send.call_args.kwargs["body"]["raw"]
        decoded = base64.urlsafe_b64decode(sent_payload).decode(
            "utf-8", errors="ignore"
        )
        self.assertIn("sam@example.com", decoded)
        self.assertIn("user@gmail.com", decoded)
