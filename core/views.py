from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import (
    Tenant,
    Payment,
    ReminderLog,
    Notification,
    MaintenanceComplaint,
    UserProfile,
    ensure_user_profile,
)
from .forms import TenantForm, PaymentForm
from .email_service import EmailReminderService


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

        tenant = Tenant.objects.create(
            name=name,
            phone=data.get("phone", "").strip(),
            email=data.get("email", "").strip(),
            property=data.get("property", "").strip(),
            rent=float(data.get("rent", 0)),
            pending=float(data.get("pending", 0)),
            due_day=int(data.get("due_day", 1)),
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
        tenant = get_object_or_404(Tenant, id=tenant_id)
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

        tenant = Tenant.objects.get(id=tenant_id)

        # Create payment record
        payment = Payment.objects.create(
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
        tenant = Tenant.objects.get(id=tenant_id)

        payments = Payment.objects.filter(tenant=tenant).order_by("-date")
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
        password = request.POST.get("password", "").strip()

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
        password = request.POST.get("password", "").strip()
        password_confirm = request.POST.get("password_confirm", "").strip()

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

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "core/register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "core/register.html")

        # Create user
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user.save()

        # Send welcome email
        EmailReminderService.send_welcome_email(user.email, user.username)

        # Auto login after registration
        login(request, user)
        messages.success(
            request, f"✅ Account created successfully! Welcome, {username}!"
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
    tenants = Tenant.objects.all().order_by("name")
    notifications = Notification.objects.order_by("-created_at")[:5]
    maintenance_complaints = MaintenanceComplaint.objects.order_by("-created_at")[:5]

    # Stats
    total = tenants.count()

    # Paid this month
    paid_this_month = tenants.filter(
        paid=True, paid_month=now.strftime("%Y-%m")
    ).count()

    # Collected amount (current month)
    collected_amount = (
        Payment.objects.filter(date__month=now.month, date__year=now.year).aggregate(
            sum=models.Sum("amount")
        )["sum"]
        or 0
    )

    # Pending count & amount
    pending_tenants = tenants.filter(paid=False)
    pending = pending_tenants.count()
    pending_amount = sum(t.total_payable() for t in pending_tenants)

    # Overdue
    overdue = tenants.filter(paid=False, due_day__lt=now.day).count()
    outstanding_amount = sum(t.total_payable() for t in tenants if not t.paid)

    # Recent payments
    payments = Payment.objects.all().order_by("-date")[:5]

    # Reminder logs
    logs = ReminderLog.objects.all().order_by("-date")[:10]

    due_tenants = tenants.filter(paid=False)[:3]
    due_tenants_count = due_tenants.count()

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
            form.save()
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

        tenant = get_object_or_404(Tenant, id=tenant_id)

        # If amount is empty, pay full (rent + pending)
        if not amount:
            amount = tenant.total_payable()
        else:
            amount = float(amount)

        # Create payment
        payment = Payment.objects.create(
            tenant=tenant, amount=amount, method=method, note=note, date=timezone.now()
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
    tenant = get_object_or_404(Tenant, id=tenant_id)
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
    )

    ReminderLog.objects.create(
        tenant=tenant,
        message=f"Manual email reminder queued for {tenant.name} for ₹{tenant.total_payable()}",
        status=result["status"],
    )

    if result["success"]:
        Notification.objects.create(
            title="Reminder email queued",
            message=f"Reminder email queued for {tenant.name}.",
            category="email",
        )
        messages.success(request, f"✅ Email reminder queued for {tenant.name}!")
    else:
        Notification.objects.create(
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
    due_tenants = Tenant.objects.filter(paid=False)
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
        )

        ReminderLog.objects.create(
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
    due_tenants = Tenant.objects.filter(paid=False)
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
        )

        ReminderLog.objects.create(
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
    tenant = get_object_or_404(Tenant, id=tenant_id)
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
    )

    ReminderLog.objects.create(
        tenant=tenant,
        message=f"Email reminder queued for {tenant.name} for ₹{tenant.total_payable()}",
        status=result["status"],
    )

    if result["success"]:
        notifications = Notification.objects.create(
            title="Email reminder sent",
            message=f"Reminder email sent to {tenant.name} ({tenant.email or 'no email'}).",
            category="email",
        )
        messages.success(request, f"✅ Email reminder queued for {tenant.name}!")
    else:
        Notification.objects.create(
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

        tenant = get_object_or_404(Tenant, id=tenant_id) if tenant_id else None
        complaint = MaintenanceComplaint.objects.create(
            tenant=tenant,
            title=title or "General maintenance issue",
            description=description or "No description provided.",
            priority=priority,
        )
        Notification.objects.create(
            title="Maintenance complaint raised",
            message=f"{complaint.title} raised for {tenant.name if tenant else 'property'}.",
            category="maintenance",
        )
        messages.success(request, "✅ Maintenance complaint submitted successfully!")
        return redirect("core:dashboard")

    return redirect("core:dashboard")


@login_required(login_url="core:login")
def notifications(request):
    items = Notification.objects.order_by("-created_at")[:20]
    return render(request, "core/notifications.html", {"notifications": items})


@login_required(login_url="core:login")
def delete_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    tenant.delete()
    messages.success(request, f"Tenant deleted successfully!")
    return redirect("core:dashboard")


@login_required(login_url="core:login")
def user_profile(request):
    """Display user profile with their data."""
    user = request.user
    profile = ensure_user_profile(user)

    context = {
        "user": user,
        "profile": profile,
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
