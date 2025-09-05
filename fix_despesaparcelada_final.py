import os
import django
import psycopg2
from psycopg2 import sql

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.conf import settings

def fix_despesaparcelada_table_final():
    """Corrige definitivamente a estrutura da tabela financas_despesaparcelada"""
    
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
            print("Corrigindo estrutura final da tabela financas_despesaparcelada...")
            
            # Verificar quais campos existem
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'financas_despesaparcelada'
            """)
            
            campos_existentes = [row[0] for row in cursor.fetchall()]
            print(f"Campos existentes: {campos_existentes}")
            
            # Se ambos data_inicio e data_primeira_parcela existem, remover data_primeira_parcela e renomear data_inicio
            if 'data_inicio' in campos_existentes and 'data_primeira_parcela' in campos_existentes:
                print("Removendo coluna duplicada 'data_primeira_parcela'...")
                cursor.execute("ALTER TABLE financas_despesaparcelada DROP COLUMN data_primeira_parcela")
                
                print("Renomeando 'data_inicio' para 'data_primeira_parcela'...")
                cursor.execute("ALTER TABLE financas_despesaparcelada RENAME COLUMN data_inicio TO data_primeira_parcela")
            
            # Se só data_inicio existe, renomear
            elif 'data_inicio' in campos_existentes and 'data_primeira_parcela' not in campos_existentes:
                print("Renomeando 'data_inicio' para 'data_primeira_parcela'...")
                cursor.execute("ALTER TABLE financas_despesaparcelada RENAME COLUMN data_inicio TO data_primeira_parcela")
            
            conn.commit()
            print("Correção concluída com sucesso!")
            
            # Verificar estrutura final
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'financas_despesaparcelada'
                ORDER BY ordinal_position
            """)
            
            print("\nEstrutura final da tabela financas_despesaparcelada:")
            for row in cursor.fetchall():
                print(f"  {row[0]} - {row[1]} - Nullable: {row[2]} - Default: {row[3]}")
            
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
    fix_despesaparcelada_table_final()