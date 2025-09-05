import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def fix_tenant_table():
    try:
        cursor = connection.cursor()
        
        print("🔧 Adicionando campos faltantes na tabela financas_tenant...")
        
        # Lista de campos para adicionar
        fields_to_add = [
            ('codigo', 'VARCHAR(20) UNIQUE NOT NULL DEFAULT \'\''),
            ('ativo', 'BOOLEAN DEFAULT TRUE'),
            ('criado_em', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'),
            ('atualizado_em', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
        ]
        
        for field_name, field_definition in fields_to_add:
            try:
                cursor.execute(f"""
                    ALTER TABLE financas_tenant 
                    ADD COLUMN IF NOT EXISTS {field_name} {field_definition};
                """)
                print(f"  ✅ Campo {field_name} adicionado")
            except Exception as e:
                print(f"  ⚠️ Campo {field_name}: {e}")
        
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
            print(f"  - {column_name}: {data_type} (nullable: {nullable})")
        
        # Verificar se há registros na tabela
        cursor.execute("SELECT COUNT(*) FROM financas_tenant;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Registros na tabela: {count}")
        
        print("\n🎉 Tabela financas_tenant atualizada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_tenant_table()