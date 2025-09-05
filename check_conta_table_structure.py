import os
import django
import psycopg2
from psycopg2 import sql

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.conf import settings

def check_conta_table():
    """Verifica a estrutura da tabela financas_conta"""
    
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
            print("Verificando estrutura da tabela financas_conta...")
            
            # Verificar estrutura da tabela
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'financas_conta'
                ORDER BY ordinal_position
            """)
            
            print("\nEstrutura atual da tabela financas_conta:")
            for row in cursor.fetchall():
                print(f"  {row[0]} - {row[1]} - Nullable: {row[2]} - Default: {row[3]}")
            
            # Verificar constraints
            cursor.execute("""
                SELECT conname, contype, pg_get_constraintdef(oid) as definition
                FROM pg_constraint 
                WHERE conrelid = 'financas_conta'::regclass
            """)
            
            print("\nConstraints da tabela:")
            for row in cursor.fetchall():
                print(f"  {row[0]} - Tipo: {row[1]} - Definição: {row[2]}")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM financas_conta")
            count = cursor.fetchone()[0]
            print(f"\nTotal de registros: {count}")
            
            # Verificar se existe campo banco_id
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'financas_conta' 
                AND column_name = 'banco_id'
            """)
            
            banco_id_exists = cursor.fetchone()
            print(f"\nCampo 'banco_id' existe: {bool(banco_id_exists)}")
            
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_conta_table()