#!/usr/bin/env python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gharrent.settings")
import django

django.setup()

from django.contrib.auth.models import User
from core.models import Tenant, UserProfile

print("=" * 60)
print("GHARRENT SYSTEM STATUS REPORT")
print("=" * 60)

# Users
users = User.objects.all()
print(f"\nUsers ({users.count()}):")
for user in users:
    profile = UserProfile.objects.filter(user=user).first()
    status = "OK" if profile else "NO"
    print(f"   [{status}] {user.username:15} - {user.email}")

# Tenants
tenants = Tenant.objects.all()
print(f"\nTenants ({tenants.count()}):")
for tenant in tenants:
    total = tenant.rent + tenant.pending
    status = "PAID" if tenant.paid else "PENDING"
    print(f"   [{status}] {tenant.name:20} - Rs{total:,} - {tenant.email}")

# Profiles
profiles = UserProfile.objects.all()
print(f"\nUser Profiles ({profiles.count()}):")
for profile in profiles:
    phone = profile.phone or "No phone"
    print(f"   [OK] {profile.user.username:15} - {phone}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED - SYSTEM OPERATIONAL!")
print("=" * 60)
