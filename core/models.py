import logging
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import connection, models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

MAX_MONEY_VALUE = Decimal("9999999.99")
MIN_MONEY_VALUE = Decimal("0.00")


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
    rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(MIN_MONEY_VALUE),
            MaxValueValidator(MAX_MONEY_VALUE),
        ],
    )
    pending = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        validators=[
            MinValueValidator(MIN_MONEY_VALUE),
            MaxValueValidator(MAX_MONEY_VALUE),
        ],
    )
    due_day = models.PositiveSmallIntegerField()  # 1–31
    paid = models.BooleanField(default=False)
    paid_month = models.CharField(max_length=7, blank=True, null=True)  # '2026-08'

    @staticmethod
    def parse_money(value, field_name="amount"):
        """Return a clean Decimal or None for invalid legacy values."""
        if value in (None, ""):
            return None

        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            logger.warning("Invalid %s value encountered: %r", field_name, value)
            return None

        if not parsed.is_finite():
            logger.warning("Non-finite %s value encountered: %r", field_name, value)
            return None

        if parsed < MIN_MONEY_VALUE:
            logger.warning("Negative %s value encountered: %r", field_name, value)
            return None

        if parsed > MAX_MONEY_VALUE:
            logger.warning(
                "Out-of-range %s value encountered: %r (max %s)",
                field_name,
                value,
                MAX_MONEY_VALUE,
            )
            return None

        return parsed.quantize(Decimal("0.01"))

    @classmethod
    def validate_money_value(cls, value, field_name):
        if value in (None, ""):
            raise ValidationError({field_name: "This field is required."})

        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError({field_name: "Enter a valid monetary value."})

        if not parsed.is_finite():
            raise ValidationError({field_name: "Enter a valid monetary value."})

        if parsed < MIN_MONEY_VALUE:
            raise ValidationError(
                {field_name: f"{field_name.title()} cannot be negative."}
            )

        if parsed > MAX_MONEY_VALUE:
            raise ValidationError(
                {
                    field_name: (
                        f"{field_name.title()} must be less than or equal to "
                        f"₹{MAX_MONEY_VALUE:,.2f}."
                    )
                }
            )

        quantized = parsed.quantize(Decimal("0.01"))
        if parsed != quantized:
            raise ValidationError(
                {
                    field_name: f"{field_name.title()} must have at most 2 decimal places."
                }
            )

        return quantized

    def clean(self):
        super().clean()
        self.rent = self.validate_money_value(self.rent, "rent")
        self.pending = self.validate_money_value(self.pending, "pending")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def total_payable(self):
        rent = self.parse_money(self.rent, "rent")
        pending = self.parse_money(self.pending, "pending")

        if rent is None or pending is None:
            logger.warning(
                "Tenant %s (id=%s) has invalid money values: rent=%r pending=%r; returning 0.00 to protect dashboard.",
                self.name,
                self.pk,
                self.rent,
                self.pending,
            )
            return Decimal("0.00")

        return rent + pending

    @classmethod
    def get_safe_tenants_for_user(cls, user):
        """Return valid tenant rows only; skip malformed legacy records."""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, rent, pending, name, paid FROM core_tenant WHERE user_id = %s ORDER BY name",
                [user.pk],
            )
            rows = cursor.fetchall()

        safe_ids = []
        for tenant_id, rent_value, pending_value, name, paid in rows:
            if cls.parse_money(rent_value, "rent") is None:
                logger.warning(
                    "Skipping tenant %s (id=%s) with invalid rent=%r while loading dashboard data.",
                    name,
                    tenant_id,
                    rent_value,
                )
                continue
            if cls.parse_money(pending_value, "pending") is None:
                logger.warning(
                    "Skipping tenant %s (id=%s) with invalid pending=%r while loading dashboard data.",
                    name,
                    tenant_id,
                    pending_value,
                )
                continue
            safe_ids.append(tenant_id)

        if not safe_ids:
            return []

        return list(cls.objects.filter(pk__in=safe_ids).order_by("name"))

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
