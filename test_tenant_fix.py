import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Tenant, CustomUser, Conta, Categoria
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

print("=== Testing Tenant Assignment Fix ===")

# Get user ID 3 (souzac3)
user = User.objects.get(id=3)
print(f"Testing with user: {user.username} (ID: {user.id})")

# Get user's tenant
user_tenant = user.tenants.first()
print(f"User's tenant: {user_tenant.codigo} (ID: {user_tenant.id})")

# Simulate middleware behavior
connection.tenant_id = user_tenant.id
connection.schema_name = user.schema_name
print(f"Set connection.tenant_id = {connection.tenant_id}")
print(f"Set connection.schema_name = {connection.schema_name}")

# Test creating a category (should use tenant_id automatically)
print("\n=== Testing Category Creation ===")
try:
    test_categoria = Categoria.objects.create(
        nome="Test Category for Tenant Fix",
        cor="#FF5733",
        tipo="despesa"
    )
    print(f"Category created successfully:")
    print(f"  - ID: {test_categoria.id}")
    print(f"  - Name: {test_categoria.nome}")
    print(f"  - Tenant ID: {test_categoria.tenant_id}")
    
    # Verify it was created with correct tenant_id
    if test_categoria.tenant_id == user_tenant.id:
        print("✅ SUCCESS: Category created with correct tenant_id")
    else:
        print(f"❌ ERROR: Expected tenant_id {user_tenant.id}, got {test_categoria.tenant_id}")
        
except Exception as e:
    print(f"❌ ERROR creating category: {e}")

# Test creating a conta (account)
print("\n=== Testing Account Creation ===")
try:
    test_conta = Conta.objects.create(
        nome="Test Account for Tenant Fix",
        saldo=100.00,
        tipo="corrente"
    )
    print(f"Account created successfully:")
    print(f"  - ID: {test_conta.id}")
    print(f"  - Name: {test_conta.nome}")
    print(f"  - Tenant ID: {test_conta.tenant_id}")
    
    # Verify it was created with correct tenant_id
    if test_conta.tenant_id == user_tenant.id:
        print("✅ SUCCESS: Account created with correct tenant_id")
    else:
        print(f"❌ ERROR: Expected tenant_id {user_tenant.id}, got {test_conta.tenant_id}")
        
except Exception as e:
    print(f"❌ ERROR creating account: {e}")

# Clean up test data
print("\n=== Cleaning up test data ===")
try:
    if 'test_categoria' in locals():
        test_categoria.delete()
        print("Test category deleted")
    if 'test_conta' in locals():
        test_conta.delete()
        print("Test account deleted")
except Exception as e:
    print(f"Error during cleanup: {e}")

print("\n=== Test Complete ===")