#!/usr/bin/env python
"""Test profile picture upload"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gharrent.settings")
django.setup()

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from core.models import UserProfile

# Get Amit user
user = User.objects.get(username="Amit")
profile = user.profile

# Create a test image (1x1 PNG)
png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

# Save the image
profile.profile_picture.save("test_avatar.png", ContentFile(png_data), save=True)

print(f"✅ Profile picture uploaded!")
print(f"   File: {profile.profile_picture.name}")
print(f"   Path: {profile.profile_picture.path if profile.profile_picture else 'None'}")
print(f"   URL: {profile.profile_picture.url if profile.profile_picture else 'None'}")

# Check file exists
if profile.profile_picture:
    actual_path = profile.profile_picture.path
    file_exists = os.path.exists(actual_path)
    print(f"   File exists on disk: {file_exists}")
