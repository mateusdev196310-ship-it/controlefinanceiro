import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def fix_banco_table():
    try:
        cursor = connection.cursor()
        
        print("🔧 Adicionando campo 'imagem' na tabela financas_banco...")
        
        # Adicionar campo imagem
        try:
            cursor.execute("""
                ALTER TABLE financas_banco 
                ADD COLUMN IF NOT EXISTS imagem VARCHAR(200);
            """)
            print("  ✅ Campo 'imagem' adicionado")
        except Exception as e:
            print(f"  ⚠️ Campo imagem: {e}")
        
        # Verificar estrutura final da tabela
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'financas_banco'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"\n📋 Estrutura final da tabela financas_banco ({len(columns)} campos):")
        for column_name, data_type, nullable, default in columns:
            print(f"  - {column_name}: {data_type} (nullable: {nullable})")
        
        # Verificar se há registros na tabela
        cursor.execute("SELECT COUNT(*) FROM financas_banco;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Registros na tabela: {count}")
        
        print("\n🎉 Tabela financas_banco atualizada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_banco_table()