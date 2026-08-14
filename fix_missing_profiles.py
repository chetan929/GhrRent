#!/usr/bin/env python
"""Script to create missing user profiles"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gharrent.settings")
django.setup()

from core.models import UserProfile
from django.contrib.auth.models import User

print("🔍 Checking for users without profiles...")
users_without_profile = []

for user in User.objects.all():
    try:
        _ = user.profile
    except:
        users_without_profile.append(user)
        UserProfile.objects.create(user=user)
        print(f"✅ Created profile for: {user.username}")

if not users_without_profile:
    print("✅ All users already have profiles")

print("\n📊 Profile verification:")
for user in User.objects.all():
    has_pic = "Yes" if user.profile.profile_picture else "No"
    print(f"  ✓ {user.username}: Profile exists | Has picture: {has_pic}")

print("\n✅ Fix complete!")
