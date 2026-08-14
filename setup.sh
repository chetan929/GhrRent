#!/bin/bash
# GharRent Setup Script - Quick Start Guide
# This script helps you set up email configuration and run the application

echo "================================"
echo "GharRent - Setup & Start Guide"
echo "================================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created!"
    echo ""
    echo "📝 Please edit .env and add your email credentials:"
    echo "   - Uncomment your email provider section"
    echo "   - Add your email and password"
    echo "   - Save the file"
    echo ""
    read -p "Press Enter after updating .env file..."
fi

echo ""
echo "🔄 Running migrations..."
python manage.py migrate

echo ""
echo "👤 Creating admin user (if needed)..."
echo "   Run: python manage.py createsuperuser"
echo ""

echo "🚀 Starting GharRent..."
echo "   Dashboard: http://localhost:8000"
echo "   Admin:     http://localhost:8000/admin"
echo "   Login:     http://localhost:8000/login"
echo ""

python manage.py runserver
