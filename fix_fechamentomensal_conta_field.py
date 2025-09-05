import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def fix_fechamentomensal_conta_field():
    try:
        cursor = connection.cursor()
        
        print("🔧 Adicionando campo conta_id na tabela financas_fechamentomensal...")
        
        # Adicionar campo conta_id
        try:
            cursor.execute("""
                ALTER TABLE financas_fechamentomensal 
                ADD COLUMN IF NOT EXISTS conta_id INTEGER REFERENCES financas_conta(id);
            """)
            print("  ✅ Campo conta_id adicionado")
        except Exception as e:
            print(f"  ⚠️ Campo conta_id: {e}")
        
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
        
        print("\n🎉 Campo conta_id adicionado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_fechamentomensal_conta_field()