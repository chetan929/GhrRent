@echo off
REM GharRent Setup Script - Quick Start Guide for Windows
REM This script helps you set up email configuration and run the application

echo.
echo ================================
echo GharRent - Setup ^& Start Guide
echo ================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo 📋 Creating .env file from template...
    copy .env.example .env
    echo ✅ .env file created!
    echo.
    echo 📝 Please edit .env and add your email credentials:
    echo    - Uncomment your email provider section
    echo    - Add your email and password
    echo    - Save the file
    echo.
    pause
)

echo.
echo 🔄 Running migrations...
python manage.py migrate

echo.
echo 👤 Creating admin user (optional)...
echo    Run: python manage.py createsuperuser
echo.

echo 🚀 Starting GharRent...
echo    Dashboard: http://localhost:8000
echo    Admin:     http://localhost:8000/admin
echo    Login:     http://localhost:8000/login
echo.

python manage.py runserver
pause
