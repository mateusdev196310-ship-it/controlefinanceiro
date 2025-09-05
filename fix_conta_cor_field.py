import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def fix_conta_cor_field():
    try:
        cursor = connection.cursor()
        
        print("🔧 Configurando campo 'cor' na tabela financas_conta...")
        
        # Primeiro, definir um valor padrão para o campo cor
        cursor.execute("""
            ALTER TABLE financas_conta 
            ALTER COLUMN cor SET DEFAULT '#007bff';
        """)
        print("  ✅ Valor padrão definido para campo 'cor'")
        
        # Atualizar registros existentes que tenham cor NULL
        cursor.execute("""
            UPDATE financas_conta 
            SET cor = '#007bff' 
            WHERE cor IS NULL;
        """)
        print("  ✅ Registros existentes atualizados")
        
        # Verificar estrutura da tabela
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'financas_conta' AND column_name = 'cor';
        """)
        
        column_info = cursor.fetchone()
        if column_info:
            column_name, data_type, nullable, default = column_info
            print(f"\n📋 Campo cor: {data_type} (nullable: {nullable}, default: {default})")
        
        # Verificar registros na tabela
        cursor.execute("SELECT COUNT(*) FROM financas_conta;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Registros na tabela: {count}")
        
        print("\n🎉 Campo 'cor' configurado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_conta_cor_field()