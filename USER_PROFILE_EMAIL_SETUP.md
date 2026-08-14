# GharRent - User Profile & Email Implementation Guide

## ✅ Features Implemented

### 1. User Profile System
- **UserProfile Model**: Each user now has an associated profile with:
  - Phone number
  - Organization name
  - Profile picture (upload-to-media)
  - Bio/About section
  - Created and updated timestamps

- **Profile Pages**:
  - **View Profile** (`/profile/`) - Display user information
  - **Edit Profile** (`/profile/edit/`) - Update profile information with picture upload

- **Automatic Profile Creation**: A UserProfile is automatically created whenever a new user registers

### 2. Enhanced User Display
- Dashboard topbar now displays:
  - User's first name (or username if not set)
  - User's email address
  - Profile picture initials (or uploaded picture if available)
  - Clickable profile link to view full profile

### 3. Email Messaging System
Enhanced `EmailReminderService` with:
- **HTML Email Templates**: Professional formatted emails with styling
- **Rent Reminders**: Automatic rent payment reminders sent to tenant emails
- **Welcome Emails**: Automatic welcome emails sent to new registered users
- **Multiple Provider Support**: Gmail, Outlook, SendGrid, AWS SES
- **Graceful Degradation**: Works even if SMTP not configured (queues emails)

### 4. Admin Panel
All new models registered in Django admin:
- UserProfile management
- Notification viewing and filtering
- Maintenance Complaint tracking
- Better Tenant and Payment management

---

## 🚀 Setup Instructions

### Step 1: Configure Email (Important!)

1. **Copy the .env.example file to .env** (create it if it doesn't exist):
```bash
cp .env.example .env
```

2. **For Gmail (Recommended)**:
   - Enable 2-Step Verification: https://myaccount.google.com/security
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or your device)
   - Copy the 16-character app password
   
3. **Update .env file**:
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

4. **For Other Providers**:

**Outlook:**
```
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
```

**SendGrid:**
```
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.your-api-key-here
```

**AWS SES:**
```
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-ses-user
EMAIL_HOST_PASSWORD=your-ses-password
```

### Step 2: Run Migrations
```bash
python manage.py migrate
```

### Step 3: Create Admin User (First Time Only)
```bash
python manage.py createsuperuser
```

### Step 4: Start the Server
```bash
python manage.py runserver
```

---

## 📋 User Workflow

### For New Users:
1. **Register** at `http://localhost:8000/register/`
   - Automatic welcome email sent (if email configured)
   - Automatic UserProfile created
   - Auto-login to dashboard

2. **Complete Profile** at `http://localhost:8000/profile/edit/`
   - Add first/last name
   - Add phone and organization
   - Upload profile picture
   - Add bio

3. **View Profile** at `http://localhost:8000/profile/`
   - See all profile information
   - Quick access to edit profile

### For Sending Tenant Reminders:
1. **Ensure Tenant Email is Set**:
   - Add email when creating tenant
   - Update tenant with email address

2. **Send Reminder**:
   - Click "Send Reminder" button on dashboard
   - Choose email or WhatsApp
   - Confirmation message appears

3. **View Email Logs**:
   - Check Notifications panel
   - Review ReminderLog in admin panel

---

## 📧 Email Features

### Automatic Welcome Email
Sent when user registers with:
- Welcome message
- Quick start guide
- Professional HTML formatting

### Rent Reminder Emails
Sent to tenants with:
- Monthly rent amount
- Outstanding amount
- Total payable
- Professional formatting
- HTML and plain text versions

### Email Status Tracking
- **Sent**: Email successfully sent via SMTP
- **Queued**: Email queued (SMTP not configured yet)
- **Failed**: Email failed to send (check logs)
- **Skipped**: No email address provided

---

## 🔧 Template Files Created

### New Templates:
1. **`core/templates/core/profile.html`**
   - Display user profile with all information
   - Link to edit profile
   - Account information grid
   - Biography section

2. **`core/templates/core/edit_profile.html`**
   - Edit user information form
   - Profile picture upload
   - Form sections for organization
   - Save and cancel buttons

---

## 📱 New URLs

| URL | Purpose |
|-----|---------|
| `/profile/` | View user profile |
| `/profile/edit/` | Edit user profile |
| `/send-reminder/<id>/` | Send email reminder to tenant |
| `/send-all-reminders/` | Send reminders to all unpaid tenants |

---

## 🗄️ Database Models

### UserProfile
```python
user = OneToOneField(User)  # Auto-created on user registration
phone = CharField(max_length=15)
organization = CharField(max_length=200)
profile_picture = ImageField()
bio = TextField()
created_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)
```

---

## ⚙️ Configuration

### Email Backend
```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
```

### Logging
All email operations are logged to:
- Python logger: `core.email_service`
- Check logs for debugging

---

## 🐛 Troubleshooting

### Email Not Sending?
1. Check .env file exists and is configured
2. Verify EMAIL_HOST_USER is set
3. For Gmail: Make sure 2-factor auth enabled and app password used
4. Check Django logs: `python manage.py runserver 2>&1 | tee debug.log`

### Profile Picture Not Displaying?
1. Ensure MEDIA_URL and MEDIA_ROOT configured
2. Check file permissions on media folder
3. Restart Django server after upload

### Welcome Email Not Sent on Registration?
1. Check email configuration first
2. Review logs for errors
3. Welcome email only sent if SMTP configured

---

## 📝 Files Modified

- `core/models.py` - Added UserProfile model and signals
- `core/views.py` - Added profile views, updated register view
- `core/email_service.py` - Enhanced with HTML emails and welcome emails
- `core/urls.py` - Added profile routes
- `core/admin.py` - Registered new models
- `core/templates/core/dashboard.html` - Updated profile chip link
- Created: `core/templates/core/profile.html`
- Created: `core/templates/core/edit_profile.html`

---

## 🎯 Next Steps (Optional)

1. **Email Templates**: Customize email templates with your branding
2. **Profile Picture Size**: Add image compression/resizing
3. **Email Scheduling**: Set up celery for scheduled emails
4. **Two-Factor Authentication**: Add 2FA for security
5. **Email Verification**: Verify email on registration
6. **Organization Features**: Add organization permissions

---

## 💡 Tips

- Always keep your .env file secure (add to .gitignore)
- Test email sending with a test account first
- Monitor email logs in Django admin
- Use app passwords for Gmail, not your regular password
- Consider email sending limits from your provider
