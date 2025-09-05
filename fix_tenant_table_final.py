import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def fix_tenant_table_final():
    try:
        cursor = connection.cursor()
        
        print("🔧 Corrigindo estrutura final da tabela financas_tenant...")
        
        # Remover campos antigos que estão causando conflito
        old_fields_to_remove = ['created_at', 'updated_at']
        
        for field_name in old_fields_to_remove:
            try:
                cursor.execute(f"""
                    ALTER TABLE financas_tenant 
                    DROP COLUMN IF EXISTS {field_name};
                """)
                print(f"  ✅ Campo antigo {field_name} removido")
            except Exception as e:
                print(f"  ⚠️ Campo {field_name}: {e}")
        
        # Garantir que o campo codigo tenha um valor padrão válido
        cursor.execute("""
            ALTER TABLE financas_tenant 
            ALTER COLUMN codigo DROP DEFAULT;
        """)
        
        cursor.execute("""
            ALTER TABLE financas_tenant 
            ALTER COLUMN codigo SET DEFAULT '';
        """)
        
        # Verificar estrutura final da tabela
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'financas_tenant'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"\n📋 Estrutura final da tabela financas_tenant ({len(columns)} campos):")
        for column_name, data_type, nullable, default in columns:
            print(f"  - {column_name}: {data_type} (nullable: {nullable}, default: {default})")
        
        # Verificar se há registros na tabela
        cursor.execute("SELECT COUNT(*) FROM financas_tenant;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Registros na tabela: {count}")
        
        print("\n🎉 Tabela financas_tenant corrigida com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_tenant_table_final()