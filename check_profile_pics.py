#!/usr/bin/env python
"""Check profile picture status"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gharrent.settings")
django.setup()

from django.contrib.auth.models import User

print("🔍 Profile Picture Status:\n")
for user in User.objects.all():
    pic_status = (
        "✅ Uploaded"
        if user.profile.profile_picture
        else "❌ Not uploaded (using placeholder)"
    )
    print(f"  {user.username:15} - {pic_status}")
