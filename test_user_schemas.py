import os
import django
import psycopg2
from psycopg2 import sql

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

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

def test_user_schemas():
    """Testa as consultas nos schemas de usuário"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Listar todos os schemas de usuário
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name;
        """)
        
        schemas = [row[0] for row in cursor.fetchall()]
        print(f"📋 Schemas encontrados: {len(schemas)}")
        
        for schema_name in schemas:
            print(f"\n{'='*50}")
            print(f"🔍 Testando schema: {schema_name}")
            print(f"{'='*50}")
            
            # Listar views no schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = %s
                ORDER BY table_name;
            """, (schema_name,))
            
            views = [row[0] for row in cursor.fetchall()]
            print(f"📊 Views disponíveis: {views}")
            
            # Testar cada view
            for view_name in views:
                try:
                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.{view_name}")
                    count = cursor.fetchone()[0]
                    
                    # Mostrar alguns dados se existirem
                    if count > 0:
                        cursor.execute(f"SELECT * FROM {schema_name}.{view_name} LIMIT 3")
                        rows = cursor.fetchall()
                        
                        # Obter nomes das colunas
                        cursor.execute(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_schema = %s AND table_name = %s
                            ORDER BY ordinal_position;
                        """, (schema_name, view_name))
                        columns = [row[0] for row in cursor.fetchall()]
                        
                        print(f"\n  📈 {view_name}: {count} registros")
                        print(f"     Colunas: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                        
                        # Mostrar primeira linha como exemplo
                        if rows:
                            print(f"     Exemplo: {dict(zip(columns[:3], rows[0][:3]))}")
                    else:
                        print(f"\n  📭 {view_name}: 0 registros")
                        
                except Exception as e:
                    print(f"\n  ❌ Erro ao consultar {view_name}: {e}")
            
            # Teste de consulta específica
            print(f"\n🧪 Testando consultas específicas para {schema_name}:")
            
            # Teste 1: Resumo financeiro
            try:
                cursor.execute(f"SELECT * FROM {schema_name}.resumo_financeiro")
                resumo = cursor.fetchall()
                if resumo:
                    print(f"  ✅ Resumo financeiro: {len(resumo)} contas")
                else:
                    print(f"  📭 Resumo financeiro: sem dados")
            except Exception as e:
                print(f"  ❌ Erro no resumo financeiro: {e}")
            
            # Teste 2: Transações por categoria
            try:
                cursor.execute(f"SELECT * FROM {schema_name}.transacoes_por_categoria LIMIT 5")
                categorias = cursor.fetchall()
                if categorias:
                    print(f"  ✅ Transações por categoria: {len(categorias)} categorias")
                else:
                    print(f"  📭 Transações por categoria: sem dados")
            except Exception as e:
                print(f"  ❌ Erro nas transações por categoria: {e}")
        
        print(f"\n{'='*50}")
        print("📋 RESUMO DOS TESTES")
        print(f"{'='*50}")
        print(f"✅ {len(schemas)} schemas testados")
        print("\n🔧 Como usar no DBeaver:")
        print("1. Pressione F5 para atualizar a conexão")
        print("2. Expanda o nó 'Schemas' na árvore de navegação")
        print("3. Você verá os schemas user_* listados")
        print("4. Expanda cada schema para ver as views")
        print("5. Execute consultas como:")
        for schema in schemas[:2]:  # Mostrar exemplos dos primeiros 2
            print(f"   SELECT * FROM {schema}.transacoes;")
            print(f"   SELECT * FROM {schema}.resumo_financeiro;")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
    finally:
        cursor.close()
        conn.close()

def show_connection_info():
    """Mostra informações de conexão para o DBeaver"""
    from django.conf import settings
    db_config = settings.DATABASES['default']
    
    print("\n🔗 INFORMAÇÕES DE CONEXÃO PARA DBEAVER:")
    print(f"Host: {db_config['HOST']}")
    print(f"Port: {db_config['PORT']}")
    print(f"Database: {db_config['NAME']}")
    print(f"Username: {db_config['USER']}")
    print("Password: [configurada no .env]")
    print("\n📝 Schemas disponíveis para consulta:")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name;
        """)
        
        schemas = [row[0] for row in cursor.fetchall()]
        for schema in schemas:
            print(f"  - {schema}")
            
    except Exception as e:
        print(f"❌ Erro ao listar schemas: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("🧪 Testando schemas de usuário no PostgreSQL...")
    test_user_schemas()
    show_connection_info()