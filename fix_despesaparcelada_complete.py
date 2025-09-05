import os
import django
import psycopg2
from psycopg2 import sql

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.conf import settings

def fix_despesaparcelada_table():
    """Adiciona todos os campos faltantes à tabela financas_despesaparcelada"""
    
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
            print("Verificando e corrigindo estrutura da tabela financas_despesaparcelada...")
            
            # Lista de campos que devem existir
            campos_necessarios = [
                ('data_primeira_parcela', 'DATE'),
                ('dia_vencimento', 'INTEGER DEFAULT 1'),
                ('intervalo_tipo', "VARCHAR(15) DEFAULT 'mensal'"),
                ('intervalo_dias', 'INTEGER'),
                ('criada_em', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'),
                ('parcelas_geradas', 'BOOLEAN DEFAULT FALSE')
            ]
            
            # Verificar quais campos existem
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'financas_despesaparcelada'
            """)
            
            campos_existentes = [row[0] for row in cursor.fetchall()]
            print(f"Campos existentes: {campos_existentes}")
            
            # Adicionar campos faltantes
            for campo, tipo in campos_necessarios:
                if campo not in campos_existentes:
                    print(f"Adicionando campo '{campo}'...")
                    cursor.execute(f"""
                        ALTER TABLE financas_despesaparcelada 
                        ADD COLUMN {campo} {tipo}
                    """)
                else:
                    print(f"Campo '{campo}' já existe.")
            
            # Renomear data_inicio para data_primeira_parcela se necessário
            if 'data_inicio' in campos_existentes and 'data_primeira_parcela' not in campos_existentes:
                print("Renomeando 'data_inicio' para 'data_primeira_parcela'...")
                cursor.execute("""
                    ALTER TABLE financas_despesaparcelada 
                    RENAME COLUMN data_inicio TO data_primeira_parcela
                """)
            
            conn.commit()
            print("Estrutura da tabela corrigida com sucesso!")
            
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
    fix_despesaparcelada_table()