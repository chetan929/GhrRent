from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
import json

from core.email_service import EmailReminderService
from core.models import MaintenanceComplaint, Notification, Tenant


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
