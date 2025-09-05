import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Tenant, CustomUser

print("=== Checking Tenant Table ===")
print("Existing tenants:")
for tenant in Tenant.objects.all():
    users_list = [u.username for u in tenant.usuarios.all()]
    users_str = ", ".join(users_list) if users_list else "None"
    print(f"ID: {tenant.id}, Code: {tenant.codigo}, Name: {tenant.nome}, Users: {users_str}, Created: {tenant.criado_em}")

print(f"\nTotal tenants: {Tenant.objects.count()}")

print("\n=== Checking Users ===")
print("Existing users:")
for user in CustomUser.objects.all():
    tenants_list = [t.codigo for t in user.tenants.all()]
    tenants_str = ", ".join(tenants_list) if tenants_list else "None"
    print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Tenants: {tenants_str}")

print(f"\nTotal users: {CustomUser.objects.count()}")

# Check if there are users without tenants
users_without_tenants = CustomUser.objects.filter(tenants__isnull=True)
print(f"\nUsers without tenants: {users_without_tenants.count()}")
for user in users_without_tenants:
    print(f"  - ID: {user.id}, Username: {user.username}")

# Check what tenant_id is being used in the current session
from django.contrib.sessions.models import Session
from django.contrib.auth.models import AnonymousUser
print("\n=== Current Session Info ===")
print("Active sessions:")
for session in Session.objects.all():
    session_data = session.get_decoded()
    user_id = session_data.get('_auth_user_id')
    tenant_id = session_data.get('tenant_id')
    print(f"Session key: {session.session_key[:10]}..., User ID: {user_id}, Tenant ID: {tenant_id}")