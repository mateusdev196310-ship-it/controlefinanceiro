import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Tenant, CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== Fixing Missing Tenant Issue ===")

# Find user without tenant
user = User.objects.get(id=3)
print(f"User found: ID={user.id}, Username={user.username}, Email={user.email}")
print(f"Schema name: {user.schema_name}")
print(f"User tenants: {list(user.tenants.all())}")

# Check if user has schema_name but no tenant
if not user.tenants.exists():
    print("\nUser has no tenant assigned. Creating tenant...")
    
    # Create a tenant for this user
    tenant_code = f"USER_{user.username.upper()}"
    tenant_name = f"Tenant for {user.username}"
    
    # Check if tenant with this code already exists
    existing_tenant = Tenant.objects.filter(codigo=tenant_code).first()
    if existing_tenant:
        print(f"Tenant with code {tenant_code} already exists. Assigning to user...")
        tenant = existing_tenant
    else:
        print(f"Creating new tenant with code: {tenant_code}")
        tenant = Tenant.objects.create(
            codigo=tenant_code,
            nome=tenant_name,
            ativo=True
        )
        print(f"Tenant created: ID={tenant.id}, Code={tenant.codigo}, Name={tenant.nome}")
    
    # Assign user to tenant
    tenant.usuarios.add(user)
    print(f"User {user.username} assigned to tenant {tenant.codigo}")
    
    # Update user's schema_name if not set
    if not user.schema_name:
        user.schema_name = f"user_{user.id}"
        user.save()
        print(f"Updated user schema_name to: {user.schema_name}")
    
    print("\n=== Verification ===")
    print(f"User tenants after fix: {list(user.tenants.all())}")
    print(f"Tenant users: {list(tenant.usuarios.all())}")
    
else:
    print("User already has tenant(s) assigned.")
    for tenant in user.tenants.all():
        print(f"  - Tenant ID: {tenant.id}, Code: {tenant.codigo}")

print("\n=== Final Status ===")
print("All users and their tenants:")
for u in User.objects.all():
    tenant_codes = [t.codigo for t in u.tenants.all()]
    print(f"User ID {u.id} ({u.username}): {tenant_codes if tenant_codes else 'NO TENANT'}")