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

def get_user_identifier(user):
    """Retorna o identificador do usuário (CPF ou CNPJ)"""
    if user.cpf:
        return user.cpf
    elif user.cnpj:
        return user.cnpj
    else:
        return str(user.id)

def find_user_by_cpf_cnpj(cpf_cnpj):
    """Busca usuário por CPF ou CNPJ"""
    try:
        # Tentar buscar por CPF primeiro
        user = CustomUser.objects.get(cpf=cpf_cnpj)
        return user
    except CustomUser.DoesNotExist:
        try:
            # Tentar buscar por CNPJ
            user = CustomUser.objects.get(cnpj=cpf_cnpj)
            return user
        except CustomUser.DoesNotExist:
            return None

def check_and_create_schema_for_user(cpf_cnpj):
    """Verifica e cria schema para um usuário específico"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Buscar usuário pelo CPF/CNPJ
        user = find_user_by_cpf_cnpj(cpf_cnpj)
        
        if not user:
            print(f"❌ Usuário com CPF/CNPJ {cpf_cnpj} não encontrado no sistema")
            return
        
        print(f"✅ Usuário encontrado: {user.username} (CPF/CNPJ: {cpf_cnpj})")
        print(f"   Schema Name: {user.schema_name}")
        
        schema_name = f"user_{cpf_cnpj}"
        
        # Verificar se o schema já existe
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = %s;
        """, (schema_name,))
        
        existing_schema = cursor.fetchone()
        
        if existing_schema:
            print(f"📋 Schema {schema_name} já existe")
            
            # Verificar views existentes
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = %s
                ORDER BY table_name;
            """, (schema_name,))
            
            views = [row[0] for row in cursor.fetchall()]
            print(f"   Views existentes: {views}")
            
            if len(views) < 6:
                print(f"   ⚠️ Apenas {len(views)} views encontradas, recriando todas...")
                create_views_for_user(cursor, user, schema_name)
            else:
                print(f"   ✅ Todas as views estão presentes")
        else:
            print(f"🔨 Criando schema {schema_name}...")
            
            # Criar schema
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            print(f"   ✅ Schema {schema_name} criado")
            
            # Criar views
            create_views_for_user(cursor, user, schema_name)
        
        # Conceder permissões
        cursor.execute(f"GRANT USAGE ON SCHEMA {schema_name} TO PUBLIC")
        cursor.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema_name} TO PUBLIC")
        print(f"   ✅ Permissões concedidas")
        
        # Testar views
        test_views(cursor, schema_name)
        
        conn.commit()
        print(f"\n✅ Schema {schema_name} configurado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def create_views_for_user(cursor, user, schema_name):
    """Cria todas as views para um usuário"""
    schema_filter = user.schema_name
    
    views_sql = {
        'transacoes': f"""
            CREATE OR REPLACE VIEW {schema_name}.transacoes AS
            SELECT * FROM public.financas_transacao WHERE tenant_id = {user.id};
        """,
        'contas': f"""
            CREATE OR REPLACE VIEW {schema_name}.contas AS
            SELECT * FROM public.financas_conta WHERE tenant_id = {user.id};
        """,
        'categorias': f"""
            CREATE OR REPLACE VIEW {schema_name}.categorias AS
            SELECT * FROM public.financas_categoria WHERE tenant_id = {user.id};
        """,
        'despesas_parceladas': f"""
            CREATE OR REPLACE VIEW {schema_name}.despesas_parceladas AS
            SELECT * FROM public.financas_despesaparcelada WHERE tenant_id = {user.id};
        """,
        'resumo_financeiro': f"""
            CREATE OR REPLACE VIEW {schema_name}.resumo_financeiro AS
            SELECT 
                c.nome as conta,
                c.saldo as saldo_atual,
                COUNT(t.id) as total_transacoes,
                SUM(CASE WHEN t.tipo = 'receita' THEN t.valor ELSE 0 END) as total_receitas,
                SUM(CASE WHEN t.tipo = 'despesa' THEN t.valor ELSE 0 END) as total_despesas
            FROM public.financas_conta c
            LEFT JOIN public.financas_transacao t ON c.id = t.conta_id AND t.tenant_id = {user.id}
            WHERE c.tenant_id = {user.id}
            GROUP BY c.id, c.nome, c.saldo;
        """,
        'transacoes_por_categoria': f"""
            CREATE OR REPLACE VIEW {schema_name}.transacoes_por_categoria AS
            SELECT 
                cat.nome as categoria,
                t.tipo as tipo_categoria,
                COUNT(t.id) as quantidade_transacoes,
                SUM(t.valor) as valor_total
            FROM public.financas_transacao t
            JOIN public.financas_categoria cat ON t.categoria_id = cat.id
            WHERE t.tenant_id = {user.id} AND cat.tenant_id = {user.id}
            GROUP BY cat.nome, t.tipo
            ORDER BY valor_total DESC;
        """
    }
    
    for view_name, view_sql in views_sql.items():
        try:
            cursor.execute(view_sql)
            print(f"     ✅ View {view_name} criada")
        except Exception as e:
            print(f"     ❌ Erro ao criar view {view_name}: {e}")

def test_views(cursor, schema_name):
    """Testa as views criadas"""
    print(f"\n🧪 Testando views do schema {schema_name}:")
    
    views_to_test = ['transacoes', 'contas', 'categorias', 'despesas_parceladas', 'resumo_financeiro', 'transacoes_por_categoria']
    
    for view_name in views_to_test:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.{view_name}")
            count = cursor.fetchone()[0]
            print(f"   📊 {view_name}: {count} registros")
        except Exception as e:
            print(f"   ❌ Erro ao testar {view_name}: {e}")

def list_all_users_and_schemas():
    """Lista todos os usuários e seus schemas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("\n📋 USUÁRIOS CADASTRADOS NO SISTEMA:")
        print("=" * 50)
        
        users = CustomUser.objects.all().order_by('username')
        
        for user in users:
            identifier = get_user_identifier(user)
            schema_name = f"user_{identifier}"
            
            # Verificar se schema existe
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s;
            """, (schema_name,))
            
            schema_exists = cursor.fetchone() is not None
            
            status = "✅ Schema OK" if schema_exists else "❌ Schema FALTANDO"
            print(f"{identifier} - {user.username} - {status}")
        
        print("\n📋 SCHEMAS EXISTENTES NO POSTGRESQL:")
        print("=" * 50)
        
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name;
        """)
        
        schemas = [row[0] for row in cursor.fetchall()]
        for schema in schemas:
            print(f"📁 {schema}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("🔍 Verificando usuários e schemas...")
    
    # Listar todos os usuários e schemas
    list_all_users_and_schemas()
    
    # Verificar especificamente o usuário 07761784582
    cpf_novo = "07761784582"
    print(f"\n🎯 Verificando usuário específico: {cpf_novo}")
    check_and_create_schema_for_user(cpf_novo)
    
    print("\n✅ Processo concluído!")
    print("\n📝 Próximos passos:")
    print("1. Pressione F5 no DBeaver para atualizar")
    print("2. Expanda 'Schemas' para ver o novo schema")
    print(f"3. Execute: SELECT * FROM user_{cpf_novo}.transacoes")