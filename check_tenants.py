import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gharrent.settings")
django.setup()

from core.models import Tenant

# Count total tenants
all_tenants = Tenant.objects.all().order_by("-id")
print(f"\n✅ TOTAL TENANTS IN DATABASE: {all_tenants.count()}")
print("\n📋 RECENT TENANTS:")
print("-" * 70)

for tenant in all_tenants[:5]:
    print(f"ID: {tenant.id} | Name: {tenant.name}")
    print(f"  Email: {tenant.email}")
    print(f"  Phone: '{tenant.phone}' (empty: {not tenant.phone})")
    print(f"  Rent: ₹{tenant.rent} | Pending: ₹{tenant.pending}")
    print(f"  Due Day: {tenant.due_day}")
    print()
