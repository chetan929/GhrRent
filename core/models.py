from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Tenant(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tenants",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=200, blank=True, null=True)
    property = models.CharField(max_length=200, blank=True, null=True)
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    pending = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    due_day = models.PositiveSmallIntegerField()  # 1–31
    paid = models.BooleanField(default=False)
    paid_month = models.CharField(max_length=7, blank=True, null=True)  # '2026-08'

    def total_payable(self):
        return self.rent + self.pending

    def __str__(self):
        return self.name


class Payment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True,
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, default="Manual")
    note = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.tenant.name} – ₹{self.amount}"


class ReminderLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reminder_logs",
        null=True,
        blank=True,
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.SET_NULL,
        related_name="reminder_logs",
        null=True,
        blank=True,
    )
    message = models.TextField()
    status = models.CharField(
        max_length=20, choices=[("Sent", "Sent"), ("Failed", "Failed")]
    )
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else "Unknown tenant"
        return f"{tenant_name} - {self.status} at {self.date.strftime('%H:%M')}"


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=50, default="general")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


class MaintenanceComplaint(models.Model):
    STATUS_CHOICES = [
        ("Open", "Open"),
        ("In Progress", "In Progress"),
        ("Resolved", "Resolved"),
    ]
    PRIORITY_CHOICES = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="maintenance_complaints",
        null=True,
        blank=True,
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Open")
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="Medium"
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - {self.status}"


class GmailCredential(models.Model):
    """Stores a user's Gmail OAuth credentials for sending reminders."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="gmail_credential",
    )
    gmail_email = models.EmailField()
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} -> {self.gmail_email}"


class UserProfile(models.Model):
    """User profile model to store additional user information."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=15, blank=True, null=True)
    organization = models.CharField(max_length=200, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"


def ensure_user_profile(user):
    """Create a profile for legacy users or users created before the signal ran."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


# Signal to automatically create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    profile.save()
