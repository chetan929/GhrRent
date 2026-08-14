# GharRent Quick Reference Guide

## 🎯 Main Features

### User Authentication
- **Register**: `/register/` - Create new account
- **Login**: `/login/` - Login to dashboard  
- **Logout**: Top-right corner dropdown
- Auto-login after registration

### User Profile
- **View Profile**: `/profile/` or click name in top-right
- **Edit Profile**: `/profile/edit/`
- Upload profile picture
- Add phone, organization, bio

### Dashboard
- **Main View**: `/` (requires login)
- **Tenants**: View all tenants with rent status
- **Payments**: Record payments and track history
- **Notifications**: View system notifications
- **Reminders**: Send email/WhatsApp reminders

### Admin Panel
- **Access**: `/admin/` (requires staff account)
- Manage users, profiles, tenants, payments, notifications

---

## ⚙️ Configuration

### Email Setup (Required for emails)
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and add your credentials
nano .env

# 3. Add email provider settings (Gmail example):
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### First Time Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations (already done!)
python manage.py migrate

# 3. Create admin user
python manage.py createsuperuser

# 4. Start server
python manage.py runserver
```

---

## 📱 URLs & Routes

| Feature | URL | Login Required |
|---------|-----|--------|
| Register | `/register/` | No |
| Login | `/login/` | No |
| Dashboard | `/` | Yes |
| Profile | `/profile/` | Yes |
| Edit Profile | `/profile/edit/` | Yes |
| Admin | `/admin/` | Yes (staff) |
| Logout | `/logout/` | Yes |
| Send Reminder | `/send-reminder/<id>/` | Yes |
| Send All | `/send-all-reminders/` | Yes |

---

## 📧 Email Providers

### Gmail (Recommended)
1. Enable 2-Step: https://myaccount.google.com/security
2. Get App Password: https://myaccount.google.com/apppasswords
3. Use 16-char app password in .env

### Outlook
- HOST: smtp-mail.outlook.com
- PORT: 587
- Use your email and password

### SendGrid
- HOST: smtp.sendgrid.net
- USER: apikey
- PASSWORD: SG.your-api-key

### AWS SES
- HOST: email-smtp.region.amazonaws.com
- PORT: 587
- Use SES credentials

---

## 🚀 Common Commands

```bash
# Start server
python manage.py runserver

# Run migrations
python manage.py migrate

# Make migrations
python manage.py makemigrations

# Create admin user
python manage.py createsuperuser

# Access shell
python manage.py shell

# Test email
python manage.py shell
>>> from core.email_service import EmailReminderService
>>> EmailReminderService.send_email_reminder("John", "john@example.com", 5000, 1000)

# Collect static files
python manage.py collectstatic
```

---

## 🔑 Admin Credentials

After setup, create admin account:
```bash
python manage.py createsuperuser
```

You'll be asked for:
- Username: (your choice)
- Email: (your choice)
- Password: (your choice)

Admin URLs:
- Login: `http://localhost:8000/admin/login/`
- Dashboard: `http://localhost:8000/admin/`

---

## 📊 Data Models

### User
- id, username, email, password, first_name, last_name
- Auto-links to UserProfile

### UserProfile (1-to-1)
- user, phone, organization, profile_picture, bio

### Tenant
- id, name, phone, email, property, rent, pending, due_day, paid

### Payment
- id, tenant, amount, method, note, date

### Reminder Log
- id, tenant, message, status, date

### Notification
- id, title, message, category, is_read, created_at

---

## 🎨 Dashboard Features

### Left Sidebar
- Navigation menu
- Quick links to features
- Tenant search

### Top Bar
- Search bar
- Theme toggle (dark/light)
- Notifications icon
- Profile (clickable to profile page)
- Logout button

### Main Content
- Statistics cards (total tenants, collected, pending, overdue)
- Recent payments table
- Due tenants list
- Tenant management modal
- Payment recording modal

---

## 🐛 Quick Troubleshooting

### "No module named X"
```bash
pip install -r requirements.txt
```

### "Database not initialized"
```bash
python manage.py migrate
```

### "Email not sending"
1. Check .env file exists
2. Verify EMAIL_HOST_USER is set
3. For Gmail: Use app password, not regular password
4. Check debug.log for errors

### "Profile picture not showing"
1. Ensure media folder exists
2. Restart server
3. Clear browser cache (Ctrl+Shift+Delete)

### "Page not found"
1. Ensure you're logged in (for protected pages)
2. Check URL spelling
3. Run `python manage.py migrate`

---

## 📚 Documentation Files

- **IMPLEMENTATION_SUMMARY.md** - Complete feature overview
- **USER_PROFILE_EMAIL_SETUP.md** - Detailed setup guide
- **EMAIL_AUTH_SETUP.md** - Original email configuration guide
- **README.md** - Project overview (if exists)

---

## 💡 Tips

1. **Profile Picture**: JPG/PNG, 500x500px recommended, max 5MB
2. **App Passwords**: Use for Gmail, not regular password
3. **Email Testing**: Use a test email account first
4. **Admin Access**: Only admins can edit other users
5. **Backups**: Regularly backup database (db.sqlite3)

---

## 🔒 Security Reminders

- Keep .env file private (add to .gitignore)
- Never commit passwords to git
- Use app passwords for Gmail, not regular passwords
- Enable 2-Factor authentication for your email
- Regular database backups
- Don't share admin credentials

---

## 📞 Quick Help

### Email Issues
- Gmail: app password from https://myaccount.google.com/apppasswords
- Outlook: your regular email password
- Check .env file is in project root
- Verify EMAIL_HOST_USER is set

### Profile Issues
- Profile auto-created with user account
- Edit at `/profile/edit/`
- Profile picture stored in media/profile_pics/
- Max 5MB file size

### Login Issues
- Reset password: Not implemented (use admin panel)
- Create new account at `/register/`
- Check database is initialized: `python manage.py migrate`

---

## 🎓 Learning Path

1. **Beginner**: Read IMPLEMENTATION_SUMMARY.md
2. **Intermediate**: Follow USER_PROFILE_EMAIL_SETUP.md
3. **Advanced**: Edit email templates in email_service.py
4. **Expert**: Extend models and views in Django

---

## ✅ Checklist Before Going Live

- [ ] .env file configured with email
- [ ] Admin user created
- [ ] Database migrations applied
- [ ] Tested user registration
- [ ] Tested profile creation and editing
- [ ] Tested email sending (check admin > Reminder Logs)
- [ ] Tested tenant management
- [ ] Tested payment recording
- [ ] Tested mobile responsiveness
- [ ] Backed up database
- [ ] Security checks completed

---

**Last Updated**: August 13, 2026  
**Version**: 2.0 (With User Profiles & Email)  
**Maintained**: GharRent Development Team
