import os
import django
import psycopg2
from psycopg2 import sql

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.conf import settings

def fix_banco_id_nullable():
    """Altera o campo banco_id para permitir valores NULL"""
    
    # Conectar ao PostgreSQL
    conn = psycopg2.connect(
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
        database=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD']
    )
    
    try:
        with conn.cursor() as cursor:
            print("Alterando campo banco_id para permitir valores NULL...")
            
            # Alterar a coluna para permitir NULL
            cursor.execute("""
                ALTER TABLE financas_conta 
                ALTER COLUMN banco_id DROP NOT NULL
            """)
            
            conn.commit()
            print("Campo banco_id alterado com sucesso para permitir NULL!")
            
            # Verificar a alteração
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'financas_conta' 
                AND column_name = 'banco_id'
            """)
            
            result = cursor.fetchone()
            if result:
                print(f"\nCampo banco_id: {result[0]} - {result[1]} - Nullable: {result[2]} - Default: {result[3]}")
            
            # Verificar estrutura completa
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'financas_conta'
                ORDER BY ordinal_position
            """)
            
            print("\nEstrutura atualizada da tabela financas_conta:")
            for row in cursor.fetchall():
                print(f"  {row[0]} - {row[1]} - Nullable: {row[2]}")
            
    except Exception as e:
        print(f"Erro: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_banco_id_nullable()