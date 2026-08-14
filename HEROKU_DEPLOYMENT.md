# 🚀 Heroku Deployment Guide - GharRent

Everything is now configured for Heroku deployment! Follow these steps:

---

## ✅ Step 1: Install Heroku CLI

Download and install from: https://devcenter.heroku.com/articles/heroku-cli

Verify installation:
```bash
heroku --version
```

---

## ✅ Step 2: Create a Heroku Account

Go to https://www.heroku.com and create a free account.

---

## ✅ Step 3: Login to Heroku

```bash
heroku login
```

This opens a browser window. Login with your Heroku credentials.

---

## ✅ Step 4: Initialize Git Repository (if not already done)

```bash
cd d:\gharrent
git init
git add .
git commit -m "Initial commit - ready for Heroku"
```

---

## ✅ Step 5: Create Heroku App

```bash
heroku create your-app-name
```

Replace `your-app-name` with a unique name (e.g., `gharrent-rental`, `gharrent-app-2026`).

This will:
- Create the app on Heroku
- Add a git remote called `heroku`
- Give you a URL like: `https://your-app-name.herokuapp.com`

---

## ✅ Step 6: Set Environment Variables on Heroku

### Generate a Secret Key

Run this in Python to generate a strong SECRET_KEY:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Set Config Variables

```bash
# Required
heroku config:set SECRET_KEY="your-generated-secret-key-here"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="your-app-name.herokuapp.com"

# Email (Gmail example)
heroku config:set EMAIL_HOST=smtp.gmail.com
heroku config:set EMAIL_PORT=587
heroku config:set EMAIL_USE_TLS=True
heroku config:set EMAIL_HOST_USER=your-email@gmail.com
heroku config:set EMAIL_HOST_PASSWORD=your-app-password
heroku config:set DEFAULT_FROM_EMAIL=your-email@gmail.com

# CSRF
heroku config:set CSRF_TRUSTED_ORIGINS="https://your-app-name.herokuapp.com"

# Optional: Twilio (for WhatsApp)
heroku config:set TWILIO_ACCOUNT_SID=your-twilio-sid
heroku config:set TWILIO_AUTH_TOKEN=your-twilio-token
heroku config:set TWILIO_WHATSAPP_NUMBER=+1234567890
```

Verify variables:
```bash
heroku config
```

---

## ✅ Step 7: Add PostgreSQL Database

Free tier Heroku no longer includes free PostgreSQL. You have two options:

### Option A: Use SQLite (Free but limited)
Skip this step - your app will use SQLite.

### Option B: Use External PostgreSQL (Recommended)

Popular free/cheap options:
- **ElephantSQL** - https://www.elephantsql.com (FREE tier available)
- **Supabase** - https://supabase.com (FREE tier)
- **Railway** - https://railway.app

**For ElephantSQL (easiest):**
1. Create account at https://www.elephantsql.com
2. Create new instance (free tier)
3. Copy your connection URL
4. Set on Heroku:
```bash
heroku config:set DATABASE_URL="your-elephantsql-url"
```

---

## ✅ Step 8: Deploy to Heroku

```bash
git push heroku main
```

If your branch is named `master`:
```bash
git push heroku master
```

This will:
- Upload your code
- Install dependencies
- Run migrations automatically (Procfile has: `release: python manage.py migrate`)
- Start the web server

---

## ✅ Step 9: Create Superuser (Admin Account)

```bash
heroku run python manage.py createsuperuser
```

Follow the prompts to create your admin account.

---

## ✅ Step 10: View Your App

Open in browser:
```bash
heroku open
```

Or manually visit: `https://your-app-name.herokuapp.com`

---

## 📱 Access Admin Panel

Go to: `https://your-app-name.herokuapp.com/admin/`

Login with the superuser account you created.

---

## 🔍 Useful Commands

```bash
# View logs
heroku logs --tail

# Run Django commands
heroku run python manage.py shell

# Create new superuser
heroku run python manage.py createsuperuser

# Restart app
heroku restart

# View config
heroku config

# Delete app
heroku apps:destroy --app your-app-name
```

---

## 🐛 Troubleshooting

### "Application Error" on website

Check logs:
```bash
heroku logs --tail
```

### Database issues
```bash
# Reset database
heroku run python manage.py migrate --noinput

# Check migrations
heroku run python manage.py showmigrations
```

### Static files not loading

Already handled by Whitenoise middleware in settings.py.

---

## 📊 Monitor Your App

Heroku Dashboard: https://dashboard.heroku.com/apps

View:
- Dyno status
- Logs
- Config variables
- Resource usage

---

## 💡 Important Notes

1. **Free Dyno Sleep**: Heroku free tier goes to sleep after 30 mins of inactivity. Upgrade to "Hobby" ($7/month) to keep it running.

2. **Media Files**: Heroku has ephemeral storage - uploaded files get deleted when dyno restarts. Consider:
   - AWS S3
   - Cloudinary
   - DigitalOcean Spaces

3. **Email**: Using Gmail SMTP from Heroku requires "App Password", not your main Gmail password.

4. **Keep .env in Git**: You can now use .env locally without worrying - Heroku uses config variables instead.

---

## 📝 Next Steps

After deployment:
1. ✅ Test login/register
2. ✅ Test email sending (send a reminder)
3. ✅ Check admin panel works
4. ✅ Upload a profile picture
5. ✅ Test all core features

---

**You're all set! Your GharRent app is now ready for production on Heroku! 🎉**
