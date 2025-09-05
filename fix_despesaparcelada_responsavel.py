import os
import django
import psycopg2
from psycopg2 import sql

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.conf import settings

def add_responsavel_field():
    """Adiciona o campo responsavel à tabela financas_despesaparcelada"""
    
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
            print("Verificando estrutura atual da tabela financas_despesaparcelada...")
            
            # Verificar se a coluna já existe
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'financas_despesaparcelada' 
                AND column_name = 'responsavel'
            """)
            
            if cursor.fetchone():
                print("Campo 'responsavel' já existe na tabela.")
                return
            
            print("Adicionando campo 'responsavel'...")
            cursor.execute("""
                ALTER TABLE financas_despesaparcelada 
                ADD COLUMN responsavel VARCHAR(100)
            """)
            
            conn.commit()
            print("Campo 'responsavel' adicionado com sucesso!")
            
            # Verificar estrutura final
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'financas_despesaparcelada'
                ORDER BY ordinal_position
            """)
            
            print("\nEstrutura atual da tabela financas_despesaparcelada:")
            for row in cursor.fetchall():
                print(f"  {row[0]} - {row[1]} - Nullable: {row[2]} - Max Length: {row[3]}")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM financas_despesaparcelada")
            count = cursor.fetchone()[0]
            print(f"\nTotal de registros: {count}")
            
    except Exception as e:
        print(f"Erro: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_responsavel_field()