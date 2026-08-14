#!/usr/bin/env python
"""Test script to debug profile picture upload issue."""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gharrent.settings")
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile
from django.core.files.base import ContentFile
import traceback

print("=" * 60)
print("Profile Picture Upload Debugging")
print("=" * 60)

# Check all users and their profiles
print("\n1. Current Users and Profiles:")
print("-" * 40)
users = User.objects.all()
for user in users:
    profile = user.profile
    pic_status = "Has picture" if profile.profile_picture else "No picture"
    pic_name = profile.profile_picture.name if profile.profile_picture else "None"
    print(f"  {user.username:15} -> {pic_status:15} ({pic_name})")

# Check if we can save a profile picture programmatically
print("\n2. Testing Programmatic Save:")
print("-" * 40)
try:
    user = User.objects.get(username="chetan")
    profile = user.profile

    # Create a simple test image data
    test_image_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDAT\x08\x99c\xf8\x0f\x00\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

    profile.profile_picture.save(
        "test_image.png", ContentFile(test_image_data), save=True
    )
    print(f"  ✓ Successfully saved test image")
    print(f"  File path: {profile.profile_picture.name}")
    print(
        f"  File URL: {profile.profile_picture.url if profile.profile_picture else 'N/A'}"
    )

except Exception as e:
    print(f"  ✗ Error during save: {str(e)}")
    traceback.print_exc()

# Check media directory
print("\n3. Media Directory Status:")
print("-" * 40)
media_root = r"d:\gharrent\media"
profile_pics_dir = os.path.join(media_root, "profile_pics")

if os.path.exists(profile_pics_dir):
    print(f"  ✓ Media directory exists: {profile_pics_dir}")
    files = os.listdir(profile_pics_dir)
    print(f"  Files in profile_pics/:")
    for f in files:
        file_path = os.path.join(profile_pics_dir, f)
        size = os.path.getsize(file_path)
        print(f"    - {f} ({size} bytes)")
else:
    print(f"  ✗ Media directory does not exist: {profile_pics_dir}")

# Check if Pillow can handle images
print("\n4. Pillow/Image Handling:")
print("-" * 40)
try:
    from PIL import Image

    print(f"  ✓ Pillow is installed")
    # Try to open existing image
    test_img_path = os.path.join(profile_pics_dir, "test_avatar.png")
    if os.path.exists(test_img_path):
        img = Image.open(test_img_path)
        print(f"  ✓ Can open images: {img.format} {img.size}")
except ImportError:
    print(f"  ✗ Pillow not installed")
except Exception as e:
    print(f"  ✗ Error with Pillow: {str(e)}")

print("\n" + "=" * 60)
