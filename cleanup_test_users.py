#!/usr/bin/env python
import os
import sys
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser, Tenant
from django.contrib.auth.models import User

def cleanup_test_users():
    """
    Remove usuários de teste mantendo apenas:
    - admin (superuser)
    - mateus
    - souzac3
    
    Remove também schemas e dados relacionados.
    """
    print("🧹 Iniciando limpeza de usuários de teste...")
    
    # Usuários que devem ser mantidos
    usuarios_manter = ['admin', 'mateus', 'souzac3']
    
    try:
        # 1. Listar todos os usuários atuais
        print("\n📋 Usuários atuais no sistema:")
        todos_usuarios = CustomUser.objects.all()
        for user in todos_usuarios:
            print(f"  - ID: {user.id}, Username: {user.username}, Email: {user.email}")
        
        # 2. Identificar usuários para remoção
        usuarios_remover = CustomUser.objects.exclude(username__in=usuarios_manter)
        print(f"\n🎯 Usuários que serão removidos: {usuarios_remover.count()}")
        
        for user in usuarios_remover:
            print(f"  - {user.username} (ID: {user.id})")
        
        if usuarios_remover.count() == 0:
            print("✅ Nenhum usuário de teste encontrado para remoção.")
            return
        
        # 3. Confirmar operação
        confirmacao = input("\n⚠️  Confirma a remoção destes usuários? (digite 'SIM' para confirmar): ")
        if confirmacao != 'SIM':
            print("❌ Operação cancelada pelo usuário.")
            return
        
        # 4. Remover tenants e dados relacionados
        print("\n🗑️  Removendo tenants e dados relacionados...")
        
        with connection.cursor() as cursor:
            for user in usuarios_remover:
                try:
                    # Buscar tenants do usuário
                    tenants_usuario = user.tenants.all()
                    
                    for tenant in tenants_usuario:
                        print(f"  📦 Removendo dados do tenant {tenant.codigo} (ID: {tenant.id})")
                        
                        # Remover dados das tabelas relacionadas ao tenant
                        cursor.execute("DELETE FROM financas_transacao WHERE tenant_id = %s", [tenant.id])
                        cursor.execute("DELETE FROM financas_despesaparcelada WHERE tenant_id = %s", [tenant.id])
                        cursor.execute("DELETE FROM financas_fechamentomensal WHERE tenant_id = %s", [tenant.id])
                        cursor.execute("DELETE FROM financas_configuracaofechamento WHERE tenant_id = %s", [tenant.id])
                        cursor.execute("DELETE FROM financas_conta WHERE tenant_id = %s", [tenant.id])
                        cursor.execute("DELETE FROM financas_categoria WHERE tenant_id = %s", [tenant.id])
                        cursor.execute("DELETE FROM financas_banco WHERE tenant_id = %s", [tenant.id])
                        
                        # Remover o tenant
                        cursor.execute("DELETE FROM financas_tenant WHERE id = %s", [tenant.id])
                        
                        print(f"  ✅ Tenant {tenant.codigo} removido com sucesso")
                        
                except Exception as e:
                    print(f"  ❌ Erro ao remover dados do usuário {user.username}: {e}")
                    continue
        
        # 5. Remover usuários
        print("\n👤 Removendo usuários...")
        usuarios_removidos = []
        
        for user in usuarios_remover:
            try:
                username = user.username
                user.delete()
                usuarios_removidos.append(username)
                print(f"  ✅ Usuário {username} removido com sucesso")
            except Exception as e:
                print(f"  ❌ Erro ao remover usuário {user.username}: {e}")
        
        # 6. Remover schemas individuais (se existirem)
        print("\n🏗️  Verificando schemas individuais...")
        
        with connection.cursor() as cursor:
            # Listar todos os schemas
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'public')
                ORDER BY schema_name;
            """)
            
            schemas = cursor.fetchall()
            schemas_manter = ['mateus', 'souzac3']  # Schemas que devem ser mantidos
            
            for (schema_name,) in schemas:
                if schema_name not in schemas_manter:
                    try:
                        print(f"  🗑️  Removendo schema: {schema_name}")
                        cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                        print(f"  ✅ Schema {schema_name} removido com sucesso")
                    except Exception as e:
                        print(f"  ❌ Erro ao remover schema {schema_name}: {e}")
        
        # 7. Relatório final
        print("\n📊 RELATÓRIO FINAL:")
        print(f"  ✅ Usuários removidos: {len(usuarios_removidos)}")
        for username in usuarios_removidos:
            print(f"    - {username}")
        
        print("\n👥 Usuários mantidos no sistema:")
        usuarios_restantes = CustomUser.objects.all()
        for user in usuarios_restantes:
            print(f"  - {user.username} (ID: {user.id})")
        
        print("\n🏗️  Schemas mantidos:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'public')
                ORDER BY schema_name;
            """)
            schemas_restantes = cursor.fetchall()
            for (schema_name,) in schemas_restantes:
                print(f"  - {schema_name}")
        
        print("\n🎉 Limpeza concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    cleanup_test_users()