import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def fix_categoria_table():
    try:
        cursor = connection.cursor()
        
        print("🔧 Adicionando campos faltantes na tabela financas_categoria...")
        
        # Adicionar campo tipo
        try:
            cursor.execute("""
                ALTER TABLE financas_categoria 
                ADD COLUMN IF NOT EXISTS tipo VARCHAR(10) DEFAULT 'ambos';
            """)
            print("  ✅ Campo 'tipo' adicionado")
        except Exception as e:
            print(f"  ⚠️ Campo tipo: {e}")
        
        # Adicionar campo cor se não existir
        try:
            cursor.execute("""
                ALTER TABLE financas_categoria 
                ADD COLUMN IF NOT EXISTS cor VARCHAR(20) DEFAULT '#6c757d';
            """)
            print("  ✅ Campo 'cor' verificado")
        except Exception as e:
            print(f"  ⚠️ Campo cor: {e}")
        
        # Verificar estrutura final da tabela
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'financas_categoria'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"\n📋 Estrutura final da tabela financas_categoria ({len(columns)} campos):")
        for column_name, data_type, nullable, default in columns:
            print(f"  - {column_name}: {data_type} (nullable: {nullable}, default: {default})")
        
        # Verificar se há registros na tabela
        cursor.execute("SELECT COUNT(*) FROM financas_categoria;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Registros na tabela: {count}")
        
        print("\n🎉 Tabela financas_categoria atualizada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_categoria_table()