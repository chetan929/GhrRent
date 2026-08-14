# 🚀 GharRent Deployment Guide

## Overview
GharRent is a Django 5.2 property management system with email notifications, payment tracking, user profiles, and admin dashboard. This guide covers local development, testing, and production deployment.

---

## 📋 Pre-Deployment Checklist

### 1. **Development Environment Setup**
```bash
# Clone repository
git clone <repo-url>
cd gharrent

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser for admin
python manage.py createsuperuser

# Run development server
python manage.py runserver 0.0.0.0:8000
```

### 2. **Database Setup**

The project uses SQLite by default. For production, consider PostgreSQL:

```bash
# For PostgreSQL (production recommended)
pip install psycopg2-binary

# Update DATABASE in settings.py:
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

### 3. **Email Configuration**

The system uses Gmail SMTP. Configure in `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Important**: Use Gmail App Password, not your main password!
1. Enable 2FA on Gmail account
2. Generate App Password at: https://myaccount.google.com/apppasswords
3. Use this password in EMAIL_HOST_PASSWORD

---

## 🔧 Production Deployment

### **Option 1: PythonAnywhere (Easiest)**

1. **Create PythonAnywhere Account**
   - Go to pythonanywhere.com
   - Sign up for free or paid plan

2. **Upload Code**
   ```bash
   # Via Git
   git clone <repo-url> <your-pythonanywhere-username>.pythonanywhere.com
   cd <your-pythonanywhere-username>.pythonanywhere.com
   ```

3. **Configure Web App**
   - Go to "Web" tab in PythonAnywhere
   - Add new web app → Choose Python 3.13 + Django
   - Point to your project

4. **Set Virtual Environment**
   - WSGI configuration file location:
     `/var/www/<user>_pythonanywhere_com_wsgi.py`
   
5. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

6. **Database**
   - For free plan: Use SQLite (included)
   - For paid: Set up PostgreSQL

7. **Reload Web App**
   - PythonAnywhere dashboard → Web tab → Reload

### **Option 2: Heroku**

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login and Create App**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set DEBUG=False
   heroku config:set SECRET_KEY='your-secret-key'
   heroku config:set EMAIL_HOST_USER='your-email@gmail.com'
   heroku config:set EMAIL_HOST_PASSWORD='your-app-password'
   ```

4. **Configure Database**
   ```bash
   # Heroku PostgreSQL (paid)
   heroku addons:create heroku-postgresql:basic
   ```

5. **Deploy**
   ```bash
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

6. **View App**
   ```bash
   heroku open
   ```

### **Option 3: AWS/DigitalOcean (Full Control)**

#### **DigitalOcean App Platform**

1. **Create Droplet**
   - 2GB RAM minimum for Django
   - Ubuntu 22.04 LTS recommended

2. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv postgresql nginx
   ```

3. **Setup Django**
   ```bash
   git clone <repo-url>
   cd gharrent
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure PostgreSQL**
   ```bash
   sudo -u postgres createdb gharrent_db
   sudo -u postgres createuser gharrent_user
   # Set password and permissions
   ```

5. **Setup Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/gharrent
   # Configure as reverse proxy to Gunicorn
   ```

6. **Run Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn gharrent.wsgi:application --bind 0.0.0.0:8000
   ```

7. **Setup Supervisor (Process Manager)**
   ```bash
   sudo apt install supervisor
   # Create config in /etc/supervisor/conf.d/gharrent.conf
   ```

8. **SSL Certificate (Let's Encrypt)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## 🔐 Security Checklist

### **Before Production**

1. **Update Settings**
   ```python
   DEBUG = False  # CRITICAL!
   ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
   SECRET_KEY = os.environ.get('SECRET_KEY')  # Use environment variable
   ```

2. **Security Headers**
   ```python
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   SECURE_BROWSER_XSS_FILTER = True
   SECURE_CONTENT_SECURITY_POLICY = {...}
   ```

3. **Database Security**
   - Use strong passwords
   - Never commit credentials
   - Use environment variables

4. **Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

5. **Backup Database**
   ```bash
   python manage.py dumpdata > backup.json
   ```

6. **HTTPS/SSL Certificate**
   - Use Let's Encrypt for free SSL
   - Redirect HTTP to HTTPS

---

## 📊 Key Features Deployed

### **✅ Implemented**
- ✅ User authentication with Django
- ✅ Tenant management system
- ✅ Email reminders (2-day before due date)
- ✅ Welcome email for new users
- ✅ User profile with photo upload
- ✅ Profile editing capabilities
- ✅ Payment tracking API endpoints
- ✅ Admin panel with full model management
- ✅ Database auto-backup (signal-based)
- ✅ CSRF protection
- ✅ Mobile-responsive design

### **📋 Optional Enhancements**
- SMS notifications (Twilio integration)
- WhatsApp alerts
- Invoice generation (ReportLab)
- Payment gateway (Razorpay/Stripe)
- Advanced analytics dashboard
- Multi-tenant support

---

## 🧪 Testing in Production

### **Quick Health Check**
```bash
# Django system check
python manage.py check --deploy

# Test email sending
python manage.py shell
>>> from core.email_service import EmailReminderService
>>> EmailReminderService.send_email_reminder("Test Name", "test@example.com", 10000, 0)
```

### **Load Testing**
```bash
# Install Apache Bench
pip install locust

# Basic load test
locust -f locustfile.py --host=https://your-app.com
```

---

## 📈 Monitoring & Maintenance

### **Log Monitoring**
```bash
# Check Django error logs
tail -f logs/django.log

# Check access logs (Nginx)
tail -f /var/log/nginx/access.log
```

### **Database Backup**
```bash
# Daily backup script
0 2 * * * /path/to/backup.sh >> /path/to/cron.log 2>&1

# Backup script content
#!/bin/bash
DATE=$(date +"%Y%m%d_%H%M%S")
python manage.py dumpdata > /backups/gharrent_$DATE.json
```

### **Email Queue Monitoring**
```python
# Monitor ReminderLog for failed emails
from core.models import ReminderLog
failed = ReminderLog.objects.filter(status='Failed').count()
print(f"Failed emails: {failed}")
```

---

## 🆘 Troubleshooting

### **Problem: "DisallowedHost" Error**
```python
# Solution: Update ALLOWED_HOSTS in settings.py
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
```

### **Problem: Static Files Not Loading**
```bash
# Solution: Collect static files
python manage.py collectstatic --noinput
```

### **Problem: Email Not Sending**
```bash
# Check email settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.EMAIL_HOST, settings.EMAIL_PORT)
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message', 'from@example.com', ['to@example.com'])
```

### **Problem: Database Connection Failed**
```bash
# Check database credentials
python manage.py dbshell
```

---

## 📚 Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [PythonAnywhere Docs](https://www.pythonanywhere.com/help/)
- [Heroku Django Docs](https://devcenter.heroku.com/articles/django-app-configuration)
- [DigitalOcean Django Guide](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu)
- [SSL/HTTPS Setup](https://certbot.eff.org/)

---

## ✅ Deployment Verification

After deployment, verify:

```bash
✅ Site loads at https://your-domain.com
✅ Admin accessible at https://your-domain.com/admin/
✅ Login works
✅ Profile page accessible
✅ Email notifications working
✅ Database persisting data
✅ Static files (CSS/JS) loading
✅ HTTPS redirect working
✅ No error pages
✅ Logs show no errors
```

---

**Version**: 1.0  
**Last Updated**: August 2026  
**Maintained By**: GharRent Development Team
