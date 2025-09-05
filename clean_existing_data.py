import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def clean_existing_data():
    try:
        cursor = connection.cursor()
        
        print("🧹 Limpando dados existentes para teste de multi-tenancy...")
        
        # Lista de tabelas para limpar (mantendo estrutura)
        tables_to_clean = [
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
        
        for table in tables_to_clean:
            try:
                cursor.execute(f"DELETE FROM {table};")
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"  ✅ {table}: {count} registros restantes")
            except Exception as e:
                print(f"  ⚠️ {table}: {e}")
        
        # Reset sequences para IDs
        sequences_to_reset = [
            'auth_user_custom_id_seq',
            'financas_tenant_id_seq',
            'financas_categoria_id_seq',
            'financas_conta_id_seq',
            'financas_transacao_id_seq',
            'financas_despesaparcelada_id_seq'
        ]
        
        print("\n🔄 Resetando sequências de ID...")
        for seq in sequences_to_reset:
            try:
                cursor.execute(f"ALTER SEQUENCE {seq} RESTART WITH 1;")
                print(f"  ✅ {seq} resetada")
            except Exception as e:
                print(f"  ⚠️ {seq}: {e}")
        
        print("\n🎉 Limpeza concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    clean_existing_data()