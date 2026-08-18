from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.conf import settings
import json
import logging
from .models import (
    Tenant,
    Payment,
    ReminderLog,
    Notification,
    MaintenanceComplaint,
    UserProfile,
    GmailCredential,
    ensure_user_profile,
)
from .forms import TenantForm, PaymentForm
from .email_service import EmailReminderService

logger = logging.getLogger(__name__)


# API Endpoints for JSON requests
@require_http_methods(["POST"])
@login_required(login_url="core:login")
def api_add_tenant(request):
    """API endpoint to add a tenant via JSON."""
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as je:
            return JsonResponse(
                {"success": False, "message": f"Invalid JSON: {str(je)}"}, status=400
            )

        name = data.get("name", "").strip()
        if not name:
            return JsonResponse(
                {"success": False, "message": "Name is required"}, status=400
            )

        try:
            rent = Tenant.validate_money_value(data.get("rent", "0"), "rent")
            pending = Tenant.validate_money_value(
                (
                    data.get("pending", "0")
                    if data.get("pending") not in (None, "")
                    else "0"
                ),
                "pending",
            )
            due_day = int(data.get("due_day", 1))
            if not 1 <= due_day <= 31:
                raise ValueError("Due day must be between 1 and 31.")
        except (InvalidOperation, TypeError, ValueError) as exc:
            return JsonResponse({"success": False, "message": str(exc)}, status=400)
        except Exception as exc:
            return JsonResponse({"success": False, "message": str(exc)}, status=400)

        tenant = Tenant.objects.create(
            user=request.user,
            name=name,
            phone=data.get("phone", "").strip(),
            email=data.get("email", "").strip(),
            property=data.get("property", "").strip(),
            rent=rent,
            pending=pending,
            due_day=due_day,
        )

        return JsonResponse(
            {
                "success": True,
                "id": tenant.id,
                "name": tenant.name,
                "message": "Tenant added successfully!",
            }
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error: {str(e)}"}, status=400
        )


@require_http_methods(["DELETE"])
@login_required(login_url="core:login")
def api_delete_tenant(request, tenant_id):
    """API endpoint to delete a tenant via JSON."""
    try:
        tenant = get_object_or_404(Tenant, id=tenant_id, user=request.user)
        tenant.delete()
        return JsonResponse(
            {"success": True, "message": "Tenant deleted successfully!"}
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error: {str(e)}"}, status=400
        )


@require_http_methods(["POST"])
@login_required(login_url="core:login")
def api_record_payment(request):
    """API endpoint to record a payment."""
    try:
        data = json.loads(request.body)
        tenant_id = data.get("tenant_id")
        amount = Decimal(str(data.get("amount", 0)))
        note = data.get("note", "Rent payment").strip()

        tenant = get_object_or_404(Tenant, id=tenant_id, user=request.user)

        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            tenant=tenant,
            amount=amount,
            date=timezone.now(),
            note=note,
            method=data.get("method", "Online"),
        )

        # Update tenant net balance.
        # A payment lowers the outstanding balance; if the payment is smaller than
        # the total due, the balance stays negative, matching the requested UI behavior.
        total_due = tenant.rent + tenant.pending
        tenant.pending = amount - total_due
        tenant.paid = tenant.pending >= Decimal("0")
        tenant.paid_month = timezone.now().strftime("%Y-%m") if tenant.paid else None

        tenant.save()

        return JsonResponse(
            {
                "success": True,
                "payment_id": payment.id,
                "message": "Payment recorded successfully!",
            }
        )
    except Tenant.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Tenant not found"}, status=404
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error: {str(e)}"}, status=400
        )


@require_http_methods(["GET"])
@login_required(login_url="core:login")
def api_get_payments(request):
    """API endpoint to get payments for a tenant."""
    try:
        tenant_id = request.GET.get("tenant_id")
        tenant = get_object_or_404(Tenant, id=tenant_id, user=request.user)

        payments = Payment.objects.filter(tenant=tenant, user=request.user).order_by(
            "-date"
        )
        data = {
            "success": True,
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "email": tenant.email,
                "rent": float(tenant.rent),
                "pending": float(tenant.pending),
                "paid": tenant.paid,
            },
            "payments": [
                {
                    "id": p.id,
                    "amount": float(p.amount),
                    "date": p.date.isoformat(),
                    "note": p.note,
                    "method": p.method,
                }
                for p in payments
            ],
        }
        return JsonResponse(data)
    except Tenant.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Tenant not found"}, status=404
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error: {str(e)}"}, status=400
        )


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, "core/login.html")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"✅ Welcome back, {user.username}!")
            return redirect("core:dashboard")
        else:
            messages.error(request, "❌ Invalid username or password.")
            return render(request, "core/login.html")

    return render(request, "core/login.html")


def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        username = username.strip()
        email = email.strip()

        # Validation
        if not all([username, email, password, password_confirm]):
            messages.error(request, "All fields are required.")
            return render(request, "core/register.html")

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, "core/register.html")

        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, "core/register.html")

        normalized_username = username
        normalized_email = email.lower()

        if User.objects.filter(username__iexact=normalized_username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "core/register.html")

        if User.objects.filter(email__iexact=normalized_email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "core/register.html")

        # Create the user with Django's secure hashed password API.
        user = User.objects.create_user(
            username=normalized_username,
            email=normalized_email,
            password=password,
        )

        # Send welcome email only if the SMTP server actually accepts it.
        email_sent = EmailReminderService.send_welcome_email(user.email, user.username)

        # Auto login after registration
        login(request, user)
        messages.success(
            request, f"✅ Account created successfully! Welcome, {user.username}!"
        )
        if not email_sent:
            messages.warning(
                request,
                "⚠️ Your account was created, but the welcome email could not be sent. Check the SMTP configuration.",
            )
        return redirect("core:dashboard")

    return render(request, "core/register.html")


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, "✅ You have been logged out successfully.")
    return redirect("core:login")


@login_required(login_url="core:login")
def dashboard(request):
    now = timezone.now()
    profile = ensure_user_profile(request.user)
    tenants = Tenant.get_safe_tenants_for_user(request.user)
    notifications = Notification.objects.filter(user=request.user).order_by(
        "-created_at"
    )[:5]
    maintenance_complaints = MaintenanceComplaint.objects.filter(
        user=request.user
    ).order_by("-created_at")[:5]

    # Stats
    total = len(tenants)

    # Paid this month
    paid_this_month = sum(
        1
        for tenant in tenants
        if tenant.paid and tenant.paid_month == now.strftime("%Y-%m")
    )

    # Collected amount (current month)
    collected_amount = (
        Payment.objects.filter(
            user=request.user,
            date__month=now.month,
            date__year=now.year,
        ).aggregate(sum=models.Sum("amount"))["sum"]
        or 0
    )

    # Pending count & amount
    pending_tenants = [tenant for tenant in tenants if not tenant.paid]
    pending = len(pending_tenants)
    pending_amount = Decimal("0.00")
    invalid_money_records = []
    for tenant in pending_tenants:
        try:
            pending_amount += tenant.total_payable()
        except Exception as exc:
            logger.warning(
                "Skipping invalid money values for tenant %s (id=%s): %s",
                tenant.name,
                tenant.pk,
                exc,
            )
            invalid_money_records.append(tenant)

    # Overdue
    overdue = sum(
        1 for tenant in tenants if not tenant.paid and tenant.due_day < now.day
    )
    outstanding_amount = Decimal("0.00")
    for tenant in tenants:
        if tenant.paid:
            continue
        try:
            outstanding_amount += tenant.total_payable()
        except Exception as exc:
            logger.warning(
                "Skipping invalid outstanding amount for tenant %s (id=%s): %s",
                tenant.name,
                tenant.pk,
                exc,
            )
            invalid_money_records.append(tenant)

    if invalid_money_records:
        logger.warning(
            "Dashboard encountered %s tenant record(s) with invalid money values.",
            len(invalid_money_records),
        )

    # Recent payments
    payments = Payment.objects.filter(user=request.user).order_by("-date")[:5]

    # Reminder logs
    logs = ReminderLog.objects.filter(user=request.user).order_by("-date")[:10]

    due_tenants = [tenant for tenant in tenants if not tenant.paid][:3]
    due_tenants_count = len(due_tenants)

    # Format tenants data for JSON injection into template
    tenants_json_data = []
    for t in tenants:
        tenants_json_data.append(
            {
                "id": t.id,
                "name": t.name,
                "email": t.email,
                "property": t.property or "N/A",
                "rent": float(t.rent),
                "pending": float(t.pending),
                "due_day": t.due_day,
                "paid": t.paid,
                "phone": t.phone,
                "payments": [],  # Will be populated by JavaScript via API if needed
                "logs": [],  # Will be populated by JavaScript if needed
                "dueDay": t.due_day,  # Keep for backward compatibility
            }
        )

    # Format logs for JSON injection
    logs_json_data = []
    for log in logs:
        logs_json_data.append(
            {
                "id": log.id,
                "tenant": log.tenant.name if log.tenant else "Unknown",
                "message": log.message,
                "status": log.status,
                "date": log.date.isoformat(),
            }
        )

    context = {
        "tenants": tenants,
        "tenants_json_data": tenants_json_data,
        "total": total,
        "paid_this_month": paid_this_month,
        "collected_amount": collected_amount,
        "pending": pending,
        "pending_amount": pending_amount,
        "overdue": overdue,
        "outstanding_amount": outstanding_amount,
        "payments": payments,
        "logs": logs,
        "logs_json_data": logs_json_data,
        "logs_count": len(logs_json_data),
        "notifications": notifications,
        "maintenance_complaints": maintenance_complaints,
        "due_tenants": due_tenants,
        "due_tenants_count": due_tenants_count,
        "profile": profile,
        "now": now,
    }
    return render(request, "core/dashboard.html", context)


@login_required(login_url="core:login")
def add_tenant(request):
    if request.method == "POST":
        form = TenantForm(request.POST)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.user = request.user
            tenant.save()
            messages.success(request, "Tenant added successfully!")
            return redirect("core:dashboard")
        else:
            messages.error(request, "Please fix the errors below.")
    return redirect("core:dashboard")


@login_required(login_url="core:login")
def record_payment(request):
    if request.method == "POST":
        tenant_id = request.POST.get("tenant_id")
        amount = request.POST.get("amount")
        method = request.POST.get("method", "Manual")
        note = request.POST.get("note", "")

        tenant = get_object_or_404(Tenant, id=tenant_id, user=request.user)

        # If amount is empty, pay full (rent + pending)
        if not amount:
            amount = tenant.total_payable()
        else:
            amount = float(amount)

        # Create payment
        payment = Payment.objects.create(
            user=request.user,
            tenant=tenant,
            amount=amount,
            method=method,
            note=note,
            date=timezone.now(),
        )

        # Update tenant net balance to reflect the payment against the total due.
        # If payment is less than due, show the remaining shortfall as negative.
        total_due = tenant.total_payable()
        tenant.pending = Decimal(str(amount)) - total_due
        tenant.paid = tenant.pending >= Decimal("0")
        if tenant.paid:
            tenant.paid_month = timezone.now().strftime("%Y-%m")
        else:
            tenant.paid_month = None

        tenant.save()

        messages.success(request, f"Payment of ₹{amount} recorded for {tenant.name}!")
        return redirect("core:dashboard")

    return redirect("core:dashboard")


@login_required(login_url="core:login")
def send_reminder(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, user=request.user)
    language = request.GET.get("language", "english")
    due_date = getattr(tenant, "due_day", None)
    due_date_value = None
    if due_date is not None:
        from datetime import date

        today = date.today()
        year = today.year
        month = today.month
        max_day = 28
        try:
            import calendar

            max_day = calendar.monthrange(year, month)[1]
        except Exception:
            pass
        safe_day = max(1, min(int(due_date), max_day))
        due_date_value = date(year, month, safe_day).isoformat()

    result = EmailReminderService.send_email_reminder(
        tenant_name=tenant.name,
        tenant_email=tenant.email or "",
        rent_amount=float(tenant.rent),
        pending_amount=float(tenant.pending),
        due_date=due_date_value,
        language=language,
        user=request.user,
    )

    ReminderLog.objects.create(
        user=request.user,
        tenant=tenant,
        message=f"Manual email reminder queued for {tenant.name} for ₹{tenant.total_payable()}",
        status=result["status"],
    )

    if result["success"]:
        Notification.objects.create(
            user=request.user,
            title="Reminder email queued",
            message=f"Reminder email queued for {tenant.name}.",
            category="email",
        )
        messages.success(request, f"✅ Email reminder queued for {tenant.name}!")
    else:
        Notification.objects.create(
            user=request.user,
            title="Reminder skipped",
            message=f"No email address found for {tenant.name}.",
            category="email",
        )
        messages.warning(
            request, f"⚠️ Email reminder skipped for {tenant.name}: {result['message']}"
        )

    # Return JSON for AJAX requests, redirect for page requests
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "success": result["success"],
                "message": result["message"],
                "tenant_name": tenant.name,
                "tenant_id": tenant.id,
            }
        )

    return redirect("core:dashboard")


@login_required(login_url="core:login")
def send_auto_reminders(request):
    due_tenants = [
        tenant
        for tenant in Tenant.get_safe_tenants_for_user(request.user)
        if not tenant.paid
    ]
    sent_count = 0
    language = request.GET.get("language", "english")

    for tenant in due_tenants:
        due_date_value = None
        if getattr(tenant, "due_day", None) is not None:
            from datetime import date
            import calendar

            today = date.today()
            max_day = calendar.monthrange(today.year, today.month)[1]
            safe_day = max(1, min(int(tenant.due_day), max_day))
            due_date_value = date(today.year, today.month, safe_day).isoformat()

        result = EmailReminderService.send_email_reminder(
            tenant_name=tenant.name,
            tenant_email=tenant.email or "",
            rent_amount=float(tenant.rent),
            pending_amount=float(tenant.pending),
            due_date=due_date_value,
            language=language,
            user=request.user,
        )

        ReminderLog.objects.create(
            user=request.user,
            tenant=tenant,
            message=f"Auto email reminder queued for {tenant.name} for ₹{tenant.total_payable()}",
            status=result["status"],
        )

        if result["success"]:
            sent_count += 1

    if sent_count > 0:
        messages.success(
            request, f"✅ Auto email reminders queued for {sent_count} tenants!"
        )
    else:
        messages.info(
            request, "No auto email reminders queued. Add tenant email addresses first."
        )

    # Return JSON for AJAX requests, redirect for page requests
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "success": sent_count > 0,
                "message": (
                    f"Auto email reminders queued for {sent_count} tenants!"
                    if sent_count > 0
                    else "No auto email reminders queued."
                ),
                "count": sent_count,
            }
        )

    return redirect("core:dashboard")


@login_required(login_url="core:login")
def send_all_reminders(request):
    due_tenants = [
        tenant
        for tenant in Tenant.get_safe_tenants_for_user(request.user)
        if not tenant.paid
    ]
    count = 0
    language = request.GET.get("language", "english")

    for tenant in due_tenants:
        due_date_value = None
        if getattr(tenant, "due_day", None) is not None:
            from datetime import date
            import calendar

            today = date.today()
            max_day = calendar.monthrange(today.year, today.month)[1]
            safe_day = max(1, min(int(tenant.due_day), max_day))
            due_date_value = date(today.year, today.month, safe_day).isoformat()

        result = EmailReminderService.send_email_reminder(
            tenant_name=tenant.name,
            tenant_email=tenant.email or "",
            rent_amount=float(tenant.rent),
            pending_amount=float(tenant.pending),
            due_date=due_date_value,
            language=language,
            user=request.user,
        )

        ReminderLog.objects.create(
            user=request.user,
            tenant=tenant,
            message=f"Bulk email reminder queued for {tenant.name} for ₹{tenant.total_payable()}",
            status=result["status"],
        )
        if result["success"]:
            count += 1

    if count > 0:
        messages.success(request, f"✅ Email reminders queued to {count} tenants!")
    else:
        messages.info(
            request, "No tenants to remind. Add email addresses to enable reminders."
        )

    # Return JSON for AJAX requests, redirect for page requests
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "success": count > 0,
                "message": (
                    f"Email reminders queued to {count} tenants!"
                    if count > 0
                    else "No tenants to remind."
                ),
                "count": count,
            }
        )

    return redirect("core:dashboard")


@login_required(login_url="core:login")
def send_email_reminder(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, user=request.user)
    language = request.GET.get("language", "english")
    due_date_value = None
    if getattr(tenant, "due_day", None) is not None:
        from datetime import date
        import calendar

        today = date.today()
        max_day = calendar.monthrange(today.year, today.month)[1]
        safe_day = max(1, min(int(tenant.due_day), max_day))
        due_date_value = date(today.year, today.month, safe_day).isoformat()

    result = EmailReminderService.send_email_reminder(
        tenant_name=tenant.name,
        tenant_email=tenant.email or "",
        rent_amount=float(tenant.rent),
        pending_amount=float(tenant.pending),
        due_date=due_date_value,
        language=language,
        user=request.user,
    )

    ReminderLog.objects.create(
        user=request.user,
        tenant=tenant,
        message=f"Email reminder queued for {tenant.name} for ₹{tenant.total_payable()}",
        status=result["status"],
    )

    if result["success"]:
        Notification.objects.create(
            user=request.user,
            title="Email reminder sent",
            message=f"Reminder email sent to {tenant.name} ({tenant.email or 'no email'}).",
            category="email",
        )
        messages.success(request, f"✅ Email reminder queued for {tenant.name}!")
    else:
        Notification.objects.create(
            user=request.user,
            title="Email reminder skipped",
            message=f"No email address found for {tenant.name}.",
            category="email",
        )
        messages.warning(
            request, f"⚠️ Email reminder skipped for {tenant.name}: {result['message']}"
        )

    return redirect("core:dashboard")


@login_required(login_url="core:login")
def add_maintenance_complaint(request):
    if request.method == "POST":
        tenant_id = request.POST.get("tenant_id")
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", "Medium")

        tenant = (
            get_object_or_404(Tenant, id=tenant_id, user=request.user)
            if tenant_id
            else None
        )
        complaint = MaintenanceComplaint.objects.create(
            user=request.user,
            tenant=tenant,
            title=title or "General maintenance issue",
            description=description or "No description provided.",
            priority=priority,
        )
        Notification.objects.create(
            user=request.user,
            title="Maintenance complaint raised",
            message=f"{complaint.title} raised for {tenant.name if tenant else 'property'}.",
            category="maintenance",
        )
        messages.success(request, "✅ Maintenance complaint submitted successfully!")
        return redirect("core:dashboard")

    return redirect("core:dashboard")


@login_required(login_url="core:login")
def notifications(request):
    items = Notification.objects.filter(user=request.user).order_by("-created_at")[:20]
    return render(request, "core/notifications.html", {"notifications": items})


@login_required(login_url="core:login")
def delete_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id, user=request.user)
    tenant.delete()
    messages.success(request, f"Tenant deleted successfully!")
    return redirect("core:dashboard")


@login_required(login_url="core:login")
def user_profile(request):
    """Display user profile with their data."""
    user = request.user
    profile = ensure_user_profile(user)
    gmail_credential = getattr(user, "gmail_credential", None)

    context = {
        "user": user,
        "profile": profile,
        "gmail_connected": bool(gmail_credential),
        "gmail_email": gmail_credential.gmail_email if gmail_credential else None,
    }
    return render(request, "core/profile_new.html", context)


@login_required(login_url="core:login")
def edit_profile(request):
    """Edit user profile information."""
    user = request.user
    profile = ensure_user_profile(user)

    if request.method == "POST":
        try:
            # Update user info
            user.first_name = request.POST.get("first_name", user.first_name).strip()
            user.last_name = request.POST.get("last_name", user.last_name).strip()
            user.email = request.POST.get("email", user.email).strip()
            user.save()

            # Update profile info
            profile.phone = request.POST.get("phone", "").strip()
            profile.organization = request.POST.get("organization", "").strip()
            profile.bio = request.POST.get("bio", "").strip()[
                :500
            ]  # Limit to 500 chars

            # Handle profile picture if uploaded
            if "profile_picture" in request.FILES:
                file = request.FILES["profile_picture"]
                profile.profile_picture = file

            profile.save()

            messages.success(request, "✅ Profile updated successfully!")
            return redirect("core:user_profile")
        except Exception as e:
            messages.error(request, f"❌ Error updating profile: {str(e)}")
            # Log the error for debugging
            import traceback

            print(f"Profile update error: {traceback.format_exc()}")

    context = {
        "user": user,
        "profile": profile,
    }
    return render(request, "core/edit_profile_new.html", context)


@login_required(login_url="core:login")
def gmail_connect(request):
    """Begin the Google OAuth flow for a user's Gmail account."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.error(
            "Gmail OAuth not configured: GOOGLE_CLIENT_ID=%s, GOOGLE_CLIENT_SECRET=%s",
            bool(settings.GOOGLE_CLIENT_ID),
            bool(settings.GOOGLE_CLIENT_SECRET),
        )
        messages.error(
            request,
            "❌ Gmail OAuth is not configured. Please contact support.",
        )
        return redirect("core:user_profile")

    try:
        from google_auth_oauthlib.flow import Flow

        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=[
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/userinfo.email",
                "openid",
            ],
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            login_hint=request.user.email,
        )
        request.session["gmail_oauth_state"] = state
        logger.info("Gmail OAuth flow initiated for user %s", request.user.username)
        return redirect(authorization_url)
    except Exception as exc:
        logger.exception(
            "Gmail connect flow error for user %s: %s",
            request.user.username,
            type(exc).__name__,
        )
        messages.error(
            request, "❌ Could not start Gmail connection. Please try again."
        )
        return redirect("core:user_profile")


@login_required(login_url="core:login")
def gmail_callback(request):
    """Handle the OAuth callback and store the connected Gmail account."""
    state = request.session.get("gmail_oauth_state")
    if not state or request.GET.get("state") != state:
        logger.warning("Gmail OAuth state mismatch for user %s", request.user.username)
        messages.error(
            request, "❌ Gmail OAuth session is invalid or expired. Please try again."
        )
        return redirect("core:user_profile")

    # Check for OAuth errors (user denied permission, etc.)
    error = request.GET.get("error")
    if error:
        if error == "access_denied":
            logger.info("User %s denied Gmail OAuth permissions", request.user.username)
            messages.warning(
                request,
                "❌ You denied Gmail access. Please grant permission to connect your Gmail account.",
            )
        else:
            logger.warning(
                "Gmail OAuth error for user %s: %s",
                request.user.username,
                error,
            )
            messages.error(
                request, f"❌ Gmail connection failed: {error}. Please try again."
            )
        return redirect("core:user_profile")

    try:
        from google_auth_oauthlib.flow import Flow
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=[
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/userinfo.email",
                "openid",
            ],
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

        authorization_code = request.GET.get("code")
        if not authorization_code:
            logger.error(
                "No authorization code received in callback for user %s",
                request.user.username,
            )
            messages.error(
                request, "❌ No authorization code received. Please try again."
            )
            return redirect("core:user_profile")

        flow.fetch_token(code=authorization_code)
        credentials = flow.credentials

        if not credentials or not credentials.token:
            logger.error(
                "No access token obtained after OAuth flow for user %s",
                request.user.username,
            )
            messages.error(
                request, "❌ Failed to obtain access token. Please try again."
            )
            return redirect("core:user_profile")

        oauth_service = build("oauth2", "v2", credentials=credentials)
        email_info = oauth_service.userinfo().get().execute()
        gmail_email = email_info.get("email")

        if not gmail_email:
            logger.error(
                "Could not retrieve Gmail email address for user %s",
                request.user.username,
            )
            messages.error(
                request, "❌ Could not retrieve your Gmail email. Please try again."
            )
            return redirect("core:user_profile")

        # Preserve existing refresh token if new one is not provided
        existing_credential = getattr(request.user, "gmail_credential", None)
        refresh_token = credentials.refresh_token

        if not refresh_token and existing_credential:
            # Use existing refresh token if Google didn't return a new one
            refresh_token = existing_credential.refresh_token

        # Store or update the Gmail credential
        gmail_cred, created = GmailCredential.objects.update_or_create(
            user=request.user,
            defaults={
                "gmail_email": gmail_email,
                "access_token": credentials.token,
                "refresh_token": refresh_token,
                "token_expiry": credentials.expiry,
            },
        )

        request.session.pop("gmail_oauth_state", None)
        action = "connected" if created else "updated"
        logger.info(
            "Gmail credential %s for user %s with email %s",
            action,
            request.user.username,
            gmail_email,
        )
        messages.success(request, f"✅ Gmail account {action}: {gmail_email}")
        return redirect("core:user_profile")

    except Exception as exc:
        error_type = type(exc).__name__
        logger.exception(
            "Gmail callback error for user %s [%s]: %s",
            request.user.username,
            error_type,
            str(exc),
        )

        # Provide specific error messages for common issues
        if "invalid_grant" in str(exc):
            messages.error(
                request,
                "❌ Authorization code expired or already used. Please try connecting again.",
            )
        elif "redirect_uri_mismatch" in str(exc):
            logger.error(
                "CRITICAL: Redirect URI mismatch. Configured: %s",
                settings.GOOGLE_REDIRECT_URI,
            )
            messages.error(
                request,
                "❌ Redirect URI configuration mismatch. Please contact support.",
            )
        else:
            messages.error(request, "❌ Gmail connection failed. Please try again.")

        return redirect("core:user_profile")


@login_required(login_url="core:login")
@require_POST
def gmail_disconnect(request):
    """Remove the user's Gmail OAuth connection via POST only."""
    try:
        gmail_credential = GmailCredential.objects.get(user=request.user)
        gmail_email = gmail_credential.gmail_email
        gmail_credential.delete()
        logger.info(
            "Gmail credential disconnected for user %s (email: %s)",
            request.user.username,
            gmail_email,
        )
        messages.success(request, "✅ Gmail connection removed successfully.")
    except GmailCredential.DoesNotExist:
        logger.info(
            "Disconnect attempt for user %s with no active Gmail credential",
            request.user.username,
        )
        messages.info(request, "ℹ️ No Gmail connection was active for this account.")
    except Exception as exc:
        logger.exception(
            "Error disconnecting Gmail for user %s: %s",
            request.user.username,
            str(exc),
        )
        messages.error(request, "❌ Error removing Gmail connection. Please try again.")

    return redirect("core:user_profile")
