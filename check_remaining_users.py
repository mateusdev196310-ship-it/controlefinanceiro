#!/usr/bin/env python
import os
import sys
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser, Tenant

def check_remaining_users():
    """
    Verifica usuários restantes no sistema após a limpeza
    """
    print("👥 USUÁRIOS RESTANTES NO SISTEMA:")
    print("=" * 50)
    
    try:
        # Listar todos os usuários
        usuarios = CustomUser.objects.all().order_by('id')
        
        if usuarios.count() == 0:
            print("❌ Nenhum usuário encontrado no sistema!")
            return
        
        for user in usuarios:
            print(f"ID: {user.id:2d} | Username: {user.username:15s} | Email: {user.email:25s} | Superuser: {user.is_superuser}")
            
            # Verificar tenants do usuário
            tenants = user.tenants.all()
            if tenants.exists():
                print(f"         Tenants: {', '.join([t.codigo for t in tenants])}")
            else:
                print("         Tenants: Nenhum")
            print()
        
        print(f"\n📊 Total de usuários: {usuarios.count()}")
        
        # Verificar schemas restantes
        print("\n🏗️  SCHEMAS RESTANTES:")
        print("=" * 30)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'public')
                ORDER BY schema_name;
            """)
            
            schemas = cursor.fetchall()
            
            if not schemas:
                print("✅ Nenhum schema individual encontrado (apenas public)")
            else:
                for (schema_name,) in schemas:
                    print(f"  - {schema_name}")
        
        # Verificar tenants restantes
        print("\n🏢 TENANTS RESTANTES:")
        print("=" * 25)
        
        tenants = Tenant.objects.all().order_by('id')
        
        if tenants.count() == 0:
            print("✅ Nenhum tenant encontrado")
        else:
            for tenant in tenants:
                usuarios_tenant = tenant.usuarios.all()
                usuarios_nomes = ', '.join([u.username for u in usuarios_tenant])
                print(f"ID: {tenant.id:2d} | Código: {tenant.codigo:15s} | Usuários: {usuarios_nomes}")
        
        print(f"\n📊 Total de tenants: {tenants.count()}")
        
    except Exception as e:
        print(f"❌ Erro ao verificar usuários: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_remaining_users()