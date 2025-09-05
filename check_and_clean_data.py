import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def check_and_clean_data():
    try:
        cursor = connection.cursor()
        
        print("🔍 Verificando dados existentes...")
        
        # Verificar dados em auth_user_custom
        cursor.execute("SELECT id, username, email FROM auth_user_custom;")
        users = cursor.fetchall()
        print(f"\n👥 Usuários existentes ({len(users)}):")
        for user_id, username, email in users:
            print(f"  - ID: {user_id}, Username: {username}, Email: {email}")
        
        # Verificar dados em financas_tenant
        cursor.execute("SELECT id, nome, codigo FROM financas_tenant;")
        tenants = cursor.fetchall()
        print(f"\n🏢 Tenants existentes ({len(tenants)}):")
        for tenant_id, nome, codigo in tenants:
            print(f"  - ID: {tenant_id}, Nome: {nome}, Código: {codigo}")
        
        # Limpar TUDO forçadamente
        print("\n🧹 Limpando TODOS os dados...")
        
        # Desabilitar constraints temporariamente
        cursor.execute("SET session_replication_role = replica;")
        
        tables_to_truncate = [
            'financas_fechamentomensal',
            'financas_configuracaofechamento', 
            'financas_meta',
            'financas_despesaparcelada',
            'financas_transacao',
            'financas_conta',
            'financas_categoria',
            'financas_tenant_usuarios',
            'financas_tenant',
            'auth_user_custom_user_permissions',
            'auth_user_custom_groups',
            'auth_user_custom'
        ]
        
        for table in tables_to_truncate:
            try:
                cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                print(f"  ✅ {table} truncada")
            except Exception as e:
                print(f"  ⚠️ {table}: {e}")
        
        # Reabilitar constraints
        cursor.execute("SET session_replication_role = DEFAULT;")
        
        # Verificar se limpeza funcionou
        print("\n🔍 Verificando após limpeza...")
        cursor.execute("SELECT COUNT(*) FROM auth_user_custom;")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM financas_tenant;")
        tenant_count = cursor.fetchone()[0]
        
        print(f"  - Usuários restantes: {user_count}")
        print(f"  - Tenants restantes: {tenant_count}")
        
        if user_count == 0 and tenant_count == 0:
            print("\n🎉 Limpeza completa realizada com sucesso!")
        else:
            print("\n⚠️ Ainda há dados restantes")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_and_clean_data()