# Email & Authentication Setup Guide

## ✅ Features Added

1. **User Authentication**
   - Login page
   - Registration page
   - Logout functionality
   - Protected views (only authenticated users can access)

2. **Email Sending**
   - SMTP configuration for real email delivery
   - Automatic email reminders to tenants
   - Support for Gmail, Outlook, SendGrid, and other providers

---

## 🔐 User Authentication

### Create Admin User (First Time)

```bash
python manage.py createsuperuser
```

This creates a superuser account. You can use it to log in to the dashboard.

### Login & Registration

- **Login Page**: `http://localhost:8000/login/`
- **Register Page**: `http://localhost:8000/register/`
- **Logout**: Click the logout button (logout icon) in the top-right corner of the dashboard

---

## 📧 Email Configuration

### Option 1: Gmail (Recommended)

1. **Enable 2-Step Verification** on your Gmail account
2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy the 16-character app password
3. **Create `.env` file** in the project root:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### Option 2: Outlook

```bash
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@outlook.com
```

### Option 3: SendGrid

1. **Get API Key** from https://sendgrid.com
2. **Add to `.env`**:

```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourcompany.com
```

### Option 4: AWS SES

```bash
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-ses-username
EMAIL_HOST_PASSWORD=your-ses-password
DEFAULT_FROM_EMAIL=noreply@yourcompany.com
```

---

## 🚀 Running the App

### 1. Start Django Development Server

```bash
python manage.py runserver
```

Then open: `http://localhost:8000/`

### 2. Start JSON Server (in a new terminal)

```bash
python json_server.py
```

This runs on: `http://127.0.0.1:3000`

### 3. Full Setup (in 2 terminals)

**Terminal 1** (Django):
```bash
python manage.py runserver
```

**Terminal 2** (JSON API):
```bash
python json_server.py
```

---

## 📝 Testing Email Sending

### Send Manual Reminder to Tenant

1. Log in to the dashboard
2. Click on a tenant name
3. Click "Send Email Reminder"
4. Check tenant's email inbox

### Send Auto Reminders to All Due Tenants

1. Log in to the dashboard
2. Click "Send Auto Reminders" button
3. All tenants with `paid=False` will receive email reminders

### Check Email Logs

All email sending is logged. You can view logs in:
- Django console output
- Or check `ReminderLog` in the Django admin: `http://localhost:8000/admin/`

---

## ✨ Email Reminders Content

Tenants receive emails with:
- Monthly rent amount
- Previous outstanding balance
- Total payable amount
- Property manager contact reminder

Example:
```
Hello Amit,

This is a friendly rent reminder from GharRent.

Monthly Rent: ₹10,000
Previous Outstanding: ₹2,000
Total Payable: ₹12,000

Please clear the payment on time.

Thank you,
GharRent - Property Manager
```

---

## 🔒 Security Tips

1. **Never commit `.env` file** - It's in `.gitignore`
2. **Use App Passwords** instead of real passwords (especially for Gmail)
3. **Keep email credentials secure** - Don't share them
4. **Use strong passwords** for user accounts
5. **Change default `SECRET_KEY`** in production

---

## 🐛 Troubleshooting

### Email not sending?

Check if `EMAIL_HOST_USER` is configured:
```bash
python manage.py shell
>>> from django.conf import settings
>>> print(settings.EMAIL_HOST_USER)  # Should show your email
```

If empty, add email config to `.env` file.

### Can't log in?

Create a superuser:
```bash
python manage.py createsuperuser
```

### "SMTP error 535"?

- Gmail: Check you used App Password, not regular password
- Other: Verify email/password is correct
- Check if IMAP/SMTP is enabled in email settings

### Emails showing as "Queued"?

This means SMTP is not configured. Add `.env` file with email settings.

---

## 📚 API Endpoints

### Authentication
- `POST /login/` - User login
- `POST /register/` - Create new account
- `GET /logout/` - Logout

### Dashboard
- `GET /` - Dashboard (login required)

### Reminders
- `GET /send-email-reminder/<tenant_id>/` - Send email reminder
- `GET /send-auto-reminders/` - Send reminders to all due tenants
- `GET /send-all-reminders/` - Send bulk reminders

### Tenant Management
- `POST /add-tenant/` - Add new tenant
- `GET /delete-tenant/<tenant_id>/` - Delete tenant
- `POST /record-payment/` - Record payment

### Notifications
- `GET /notifications/` - View notifications
- `POST /add-maintenance-complaint/` - Add complaint

---

## 🎉 Done!

Your GharRent app is now ready with:
✅ User authentication (login/register)
✅ Email reminders to tenants
✅ Protected dashboard
✅ Free-first design (no SMS/WhatsApp)
✅ Maintenance complaint tracking
✅ In-app notifications

Enjoy managing properties! 🏠
