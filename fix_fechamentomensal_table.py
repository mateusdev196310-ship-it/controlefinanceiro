import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def fix_fechamentomensal_table():
    try:
        cursor = connection.cursor()
        
        print("🔧 Adicionando campos faltantes na tabela financas_fechamentomensal...")
        
        # Lista de campos para adicionar
        fields_to_add = [
            ('fechado', 'BOOLEAN DEFAULT FALSE'),
            ('eh_parcial', 'BOOLEAN DEFAULT FALSE'),
            ('data_inicio_periodo', 'DATE'),
            ('data_fim_periodo', 'DATE'),
            ('data_fechamento', 'TIMESTAMP'),
            ('criado_em', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]
        
        for field_name, field_definition in fields_to_add:
            try:
                cursor.execute(f"""
                    ALTER TABLE financas_fechamentomensal 
                    ADD COLUMN IF NOT EXISTS {field_name} {field_definition};
                """)
                print(f"  ✅ Campo {field_name} adicionado")
            except Exception as e:
                print(f"  ⚠️ Campo {field_name}: {e}")
        
        # Verificar estrutura final da tabela
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'financas_fechamentomensal'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"\n📋 Estrutura final da tabela financas_fechamentomensal ({len(columns)} campos):")
        for column_name, data_type, nullable, default in columns:
            print(f"  - {column_name}: {data_type} (nullable: {nullable}, default: {default})")
        
        # Verificar se há registros na tabela
        cursor.execute("SELECT COUNT(*) FROM financas_fechamentomensal;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Registros na tabela: {count}")
        
        print("\n🎉 Tabela financas_fechamentomensal atualizada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_fechamentomensal_table()