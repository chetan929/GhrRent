import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gharrent.settings")
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Create a test user
user, created = User.objects.get_or_create(
    username="testapi", defaults={"email": "testapi@example.com"}
)
if created:
    user.set_password("testpass123")
    user.save()

# Create a client and log in
client = Client()
client.force_login(user)

# Test the API
payload = {
    "name": "Browser Test Tenant",
    "email": "browsertest@example.com",
    "phone": "",
    "rent": 6000,
    "pending": 500,
    "due_day": 20,
}

response = client.post(
    "/api/tenants/add/", data=json.dumps(payload), content_type="application/json"
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.content.decode('utf-8')}")

# Check if tenant was created
from core.models import Tenant

tenants = Tenant.objects.filter(name="Browser Test Tenant")
print(f"Tenant created: {tenants.exists()}")
if tenants.exists():
    t = tenants.first()
    print(f"  - ID: {t.id}")
    print(f"  - Name: {t.name}")
    print(f"  - Email: {t.email}")
    print(f"  - Phone: '{t.phone}'")
    print(f"  - Rent: {t.rent}")
