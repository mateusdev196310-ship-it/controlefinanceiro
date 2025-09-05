import os
import django
import psycopg2
from psycopg2 import sql

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser

def get_db_connection():
    """Conecta ao PostgreSQL usando as configurações do Django"""
    from django.conf import settings
    db_config = settings.DATABASES['default']
    
    return psycopg2.connect(
        host=db_config['HOST'],
        database=db_config['NAME'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        port=db_config['PORT']
    )

def check_and_fix_schemas():
    """Verifica e corrige os schemas de usuário"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Listar todos os schemas existentes
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name;
        """)
        
        existing_schemas = [row[0] for row in cursor.fetchall()]
        print(f"Schemas existentes: {existing_schemas}")
        
        # Verificar views em cada schema
        for schema_name in existing_schemas:
            print(f"\n=== Verificando schema: {schema_name} ===")
            
            # Listar views no schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = %s
                ORDER BY table_name;
            """, (schema_name,))
            
            views = [row[0] for row in cursor.fetchall()]
            print(f"Views encontradas: {views}")
            
            # Se não há views, recriar
            if not views:
                print(f"Recriando views para {schema_name}...")
                recreate_views_for_schema(cursor, schema_name)
            else:
                # Verificar se as views têm dados
                for view_name in views:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.{view_name}")
                        count = cursor.fetchone()[0]
                        print(f"  {view_name}: {count} registros")
                    except Exception as e:
                        print(f"  Erro ao consultar {view_name}: {e}")
        
        # Verificar permissões
        print("\n=== Verificando permissões ===")
        cursor.execute("""
            SELECT grantee, table_schema, table_name, privilege_type
            FROM information_schema.table_privileges 
            WHERE table_schema LIKE 'user_%'
            ORDER BY table_schema, table_name;
        """)
        
        permissions = cursor.fetchall()
        for perm in permissions:
            print(f"  {perm[0]} -> {perm[1]}.{perm[2]}: {perm[3]}")
        
        conn.commit()
        print("\n✅ Verificação concluída!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def recreate_views_for_schema(cursor, schema_name):
    """Recria as views para um schema específico"""
    # Extrair tenant_id do nome do schema
    # Formato: user_12345678901 -> buscar usuário com CPF/CNPJ = 12345678901
    cpf_cnpj = schema_name.replace('user_', '')
    
    try:
        user = CustomUser.objects.get(cpf_cnpj=cpf_cnpj)
        tenant_id = user.tenant_id
        
        print(f"  Encontrado usuário {user.nome} (tenant_id: {tenant_id})")
        
        # Criar views
        views_sql = {
            'transacoes': f"""
                CREATE OR REPLACE VIEW {schema_name}.transacoes AS
                SELECT * FROM public.financas_transacao WHERE tenant_id = '{tenant_id}';
            """,
            'contas': f"""
                CREATE OR REPLACE VIEW {schema_name}.contas AS
                SELECT * FROM public.financas_conta WHERE tenant_id = '{tenant_id}';
            """,
            'categorias': f"""
                CREATE OR REPLACE VIEW {schema_name}.categorias AS
                SELECT * FROM public.financas_categoria WHERE tenant_id = '{tenant_id}';
            """,
            'despesas_parceladas': f"""
                CREATE OR REPLACE VIEW {schema_name}.despesas_parceladas AS
                SELECT * FROM public.financas_despesaparcelada WHERE tenant_id = '{tenant_id}';
            """,
            'resumo_financeiro': f"""
                CREATE OR REPLACE VIEW {schema_name}.resumo_financeiro AS
                SELECT 
                    c.nome as conta,
                    c.saldo_atual,
                    COUNT(t.id) as total_transacoes,
                    SUM(CASE WHEN t.tipo = 'receita' THEN t.valor ELSE 0 END) as total_receitas,
                    SUM(CASE WHEN t.tipo = 'despesa' THEN t.valor ELSE 0 END) as total_despesas
                FROM public.financas_conta c
                LEFT JOIN public.financas_transacao t ON c.id = t.conta_id AND t.tenant_id = '{tenant_id}'
                WHERE c.tenant_id = '{tenant_id}'
                GROUP BY c.id, c.nome, c.saldo_atual;
            """,
            'transacoes_por_categoria': f"""
                CREATE OR REPLACE VIEW {schema_name}.transacoes_por_categoria AS
                SELECT 
                    cat.nome as categoria,
                    t.tipo,
                    COUNT(t.id) as quantidade,
                    SUM(t.valor) as total_valor
                FROM public.financas_transacao t
                JOIN public.financas_categoria cat ON t.categoria_id = cat.id
                WHERE t.tenant_id = '{tenant_id}' AND cat.tenant_id = '{tenant_id}'
                GROUP BY cat.nome, t.tipo
                ORDER BY total_valor DESC;
            """
        }
        
        for view_name, view_sql in views_sql.items():
            try:
                cursor.execute(view_sql)
                print(f"    ✅ View {view_name} criada")
            except Exception as e:
                print(f"    ❌ Erro ao criar view {view_name}: {e}")
                
    except CustomUser.DoesNotExist:
        print(f"  ❌ Usuário com CPF/CNPJ {cpf_cnpj} não encontrado")
    except Exception as e:
        print(f"  ❌ Erro ao recriar views: {e}")

def grant_permissions():
    """Concede permissões necessárias nos schemas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Listar schemas de usuário
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'user_%'
        """)
        
        schemas = [row[0] for row in cursor.fetchall()]
        
        for schema_name in schemas:
            # Conceder permissões de uso no schema
            cursor.execute(f"GRANT USAGE ON SCHEMA {schema_name} TO PUBLIC")
            
            # Conceder permissões de select nas views
            cursor.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema_name} TO PUBLIC")
            
            print(f"✅ Permissões concedidas para {schema_name}")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Erro ao conceder permissões: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("🔍 Verificando e corrigindo schemas de usuário...")
    check_and_fix_schemas()
    
    print("\n🔐 Concedendo permissões...")
    grant_permissions()
    
    print("\n✅ Processo concluído! Agora você pode:")
    print("1. Atualizar a conexão no DBeaver (F5)")
    print("2. Expandir os schemas user_* para ver as views")
    print("3. Executar consultas como: SELECT * FROM user_12345678901.transacoes")