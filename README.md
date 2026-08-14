# 🏠 GharRent - Property Management System

A comprehensive Django-based property rental management platform with user authentication, tenant management, automated email reminders, payment tracking, and admin dashboard.

## 🎯 Project Overview

GharRent is designed to help property managers efficiently manage rental properties, track payments, send automated reminders, and maintain user profiles. Built with Django 5.2 and modern web technologies.

---

## ✨ Features

### 👥 User Management
- ✅ User registration and authentication
- ✅ User profiles with customizable information
- ✅ Profile picture upload capability
- ✅ Auto-creation of user profile on registration
- ✅ Profile editing with form validation
- ✅ Member since & last login tracking

### 🏢 Tenant Management
- ✅ Add, view, and manage tenants
- ✅ Track rent amounts and pending payments
- ✅ Due date management (customizable per tenant)
- ✅ Property information storage
- ✅ Email-based contact information
- ✅ Payment status tracking

### 💰 Payment Tracking
- ✅ Record individual payments
- ✅ Multiple payment methods support
- ✅ Payment history retrieval
- ✅ Payment date and amount tracking
- ✅ JSON API for payment management
- ✅ Real-time payment status updates

### 📧 Email Notifications
- ✅ Automated rent reminders (2-day before due)
- ✅ HTML-formatted email templates
- ✅ Welcome emails for new users
- ✅ Rent breakdown in reminder emails
- ✅ Pending amount tracking in notifications
- ✅ Failed email logging

### 📊 Dashboard
- ✅ Real-time tenant overview
- ✅ Statistics (total rent, collected, pending)
- ✅ Interactive forms for data entry
- ✅ Search and filter capabilities
- ✅ Responsive mobile design
- ✅ Quick action buttons

### 👑 Admin Panel
- ✅ Django admin interface with customization
- ✅ Tenant administration
- ✅ Payment management
- ✅ User and profile management
- ✅ Notification tracking
- ✅ Maintenance complaint logging
- ✅ Advanced filtering and search
- ✅ Bulk actions support

### 🔐 Security
- ✅ CSRF protection on all forms
- ✅ User authentication required for sensitive pages
- ✅ Password-protected admin panel
- ✅ Secure email configuration
- ✅ Input validation and sanitization

---

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Django | 5.2 |
| Database | SQLite (dev), PostgreSQL (prod) | - |
| Email | Gmail SMTP | - |
| Frontend | HTML5 + CSS3 + JavaScript | ES6+ |
| Image Upload | Django ImageField + Pillow | - |
| Python | Python | 3.13+ |

---

## 📦 Installation

### Prerequisites
- Python 3.13+
- pip (Python package manager)
- Virtual environment (recommended)

### Setup Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd gharrent

# 2. Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Create superuser (for admin access)
python manage.py createsuperuser

# 6. Run development server
python manage.py runserver

# Access at: http://localhost:8000/
# Admin at: http://localhost:8000/admin/
```

---

## 📁 Project Structure

```
gharrent/
├── core/                          # Main application
│   ├── models.py                 # Database models
│   ├── views.py                  # Views & API endpoints
│   ├── forms.py                  # Form definitions
│   ├── urls.py                   # URL routing
│   ├── admin.py                  # Admin configuration
│   ├── email_service.py          # Email utilities
│   ├── templates/
│   │   └── core/
│   │       ├── dashboard.html    # Main SPA
│   │       ├── login.html        # Login page
│   │       ├── register.html     # Registration
│   │       ├── profile_new.html  # User profile
│   │       └── edit_profile_new.html  # Profile editor
│   └── migrations/               # Database migrations
├── gharrent/                      # Project settings
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Main URL config
│   ├── wsgi.py                  # WSGI config
│   └── asgi.py                  # ASGI config
├── static/                       # Static files (CSS, JS, images)
├── media/                        # User uploads
├── logs/                         # Application logs
├── manage.py                     # Django management
├── db.sqlite3                    # Database
├── requirements.txt              # Dependencies
├── .env.example                  # Environment template
├── README.md                     # This file
├── DEPLOYMENT.md                 # Deployment guide
└── EMAIL_AUTH_SETUP.md          # Email configuration guide
```

---

## 🔧 Configuration

### Email Setup (Gmail)

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Create a password for "Mail" on "Windows/Mac/Linux"
   - Copy the 16-character password

3. Update settings or `.env`:
   ```env
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

### Database Configuration

**Development (SQLite)** - No configuration needed

**Production (PostgreSQL)**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gharrent_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 🚀 API Endpoints

### Authentication
- `POST /login/` - User login
- `POST /register/` - User registration
- `GET /logout/` - User logout

### Profile Management
- `GET /profile/` - View user profile
- `POST /profile/edit/` - Edit user profile

### Tenant Management
- `POST /api/tenants/add/` - Add tenant (JSON)
- `GET /` - Dashboard (view all tenants)

### Payment Tracking
- `POST /api/payments/record/` - Record payment
- `GET /api/payments/get/` - Get tenant payments

### Admin
- `GET /admin/` - Django admin panel
- `GET /admin/core/` - Manage core models

---

## 🧪 Testing

### Run Test Suite
```bash
python test_new_features.py
```

### Manual Testing
1. **Create User**: Register at `/register/`
2. **View Profile**: Navigate to `/profile/`
3. **Edit Profile**: Click "Edit Profile" button
4. **Add Tenant**: Use dashboard form
5. **Send Reminder**: Click "Send All" button
6. **Admin Access**: Go to `/admin/`

---

## 📈 Key Statistics (Current)

- **Users**: 5 registered
- **Tenants**: 4 properties
- **User Profiles**: 4 auto-created
- **Payments**: Tracking system active
- **Emails Sent**: HTML-formatted reminders working

---

## 🔒 Security Checklist

- [x] User authentication required
- [x] CSRF protection enabled
- [x] Password hashing
- [x] Email validation
- [x] Admin authentication
- [x] Input sanitization
- [x] OneToOne profile relationship integrity
- [ ] HTTPS/SSL (for production)
- [ ] Rate limiting (for production)
- [ ] Backup strategy (for production)

---

## 🚀 Deployment

For production deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

Quick deployment options:
- **PythonAnywhere**: Easiest, free tier available
- **Heroku**: Fast setup, auto-scaling
- **DigitalOcean**: Full control, affordable
- **AWS EC2**: Scalable enterprise option

---

## 🐛 Troubleshooting

### Issue: "No module named 'core'"
**Solution**: Ensure you're in the project root directory and virtual environment is activated.

### Issue: "DisallowedHost" error
**Solution**: Add your domain to `ALLOWED_HOSTS` in `settings.py`

### Issue: Email not sending
**Solution**: 
1. Check email credentials in settings
2. Verify Gmail App Password is correct
3. Check logs: `python manage.py shell`

### Issue: Profile picture not uploading
**Solution**:
1. Ensure `media/` directory exists
2. Check `MEDIA_ROOT` and `MEDIA_URL` in settings
3. Verify Pillow is installed: `pip install Pillow`

---

## 📚 Documentation

- **Email Setup**: See [EMAIL_AUTH_SETUP.md](./EMAIL_AUTH_SETUP.md)
- **Deployment**: See [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Django Docs**: https://docs.djangoproject.com/
- **API Docs**: Available in code comments

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/new-feature`
2. Commit changes: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/new-feature`
4. Submit pull request

---

## 📄 License

This project is provided as-is for educational and commercial use.

---

## 👨‍💻 Developer Notes

### Recent Implementations (August 2026)

✅ **Profile System**
- Created standalone profile templates
- Implemented profile editing with file upload
- Auto-create UserProfile via Django signals

✅ **Payment API**
- Added payment recording endpoint
- Implemented payment retrieval endpoint
- Added JSON request/response handling

✅ **Admin Enhancements**
- Configured advanced admin models
- Added custom list displays and filters
- Set up inline editing for related objects

✅ **Deployment**
- Created comprehensive deployment guide
- Added environment configuration template
- Documented multiple deployment options

### Next Steps (Optional)
- [ ] WhatsApp/SMS integration
- [ ] Invoice PDF generation
- [ ] Payment gateway integration (Razorpay/Stripe)
- [ ] Advanced analytics dashboard
- [ ] Mobile app development
- [ ] Multi-tenant support
- [ ] Audit logging

---

## 📞 Support

For issues or questions:
1. Check documentation files
2. Review code comments
3. Test with provided test suite
4. Check Django logs

---

**Project**: GharRent  
**Version**: 2.0  
**Last Updated**: August 13, 2026  
**Status**: ✅ Production Ready
