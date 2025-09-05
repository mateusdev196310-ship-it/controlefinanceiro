#!/usr/bin/env python
"""
Script melhorado para criar schemas virtuais por usuário no PostgreSQL
Com tratamento de erros e transações individuais.
"""

import os
import django
import psycopg2
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser, Tenant

def criar_schema_usuario(user, tenant):
    """
    Cria schema para um usuário específico.
    """
    db_config = settings.DATABASES['default']
    
    # Nova conexão para cada usuário
    conn = psycopg2.connect(
        host=db_config['HOST'],
        database=db_config['NAME'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        port=db_config['PORT']
    )
    conn.autocommit = True  # Autocommit para evitar problemas de transação
    
    cursor = conn.cursor()
    
    try:
        # Nome do schema baseado no CPF/CNPJ
        if user.cpf:
            schema_name = f"user_{user.cpf.replace('.', '').replace('-', '')}"
        elif user.cnpj:
            schema_name = f"user_{user.cnpj.replace('.', '').replace('/', '').replace('-', '')}"
        else:
            schema_name = f"user_{user.username}"
        
        print(f"\n👤 Criando schema: {schema_name} (usuário: {user.username})")
        
        # Criar schema
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
        print(f"   ✅ Schema {schema_name} criado")
        
        # Criar views filtradas por tenant_id
        views = [
            ('transacoes', 'financas_transacao'),
            ('contas', 'financas_conta'),
            ('categorias', 'financas_categoria'),
            ('despesas_parceladas', 'financas_despesaparcelada')
        ]
        
        for view_name, table_name in views:
            sql = f"""
            CREATE OR REPLACE VIEW {schema_name}.{view_name} AS 
            SELECT * FROM public.{table_name} 
            WHERE tenant_id = {tenant.id};
            """
            cursor.execute(sql)
            print(f"   ✅ View criada: {view_name}")
        
        # Criar view de resumo financeiro
        sql_resumo = f"""
        CREATE OR REPLACE VIEW {schema_name}.resumo_financeiro AS 
        SELECT 
            c.nome as conta,
            c.saldo,
            COUNT(t.id) as total_transacoes,
            COALESCE(SUM(CASE WHEN t.tipo = 'receita' THEN t.valor ELSE 0 END), 0) as total_receitas,
            COALESCE(SUM(CASE WHEN t.tipo = 'despesa' THEN t.valor ELSE 0 END), 0) as total_despesas
        FROM public.financas_conta c
        LEFT JOIN public.financas_transacao t ON c.id = t.conta_id AND t.tenant_id = {tenant.id}
        WHERE c.tenant_id = {tenant.id}
        GROUP BY c.id, c.nome, c.saldo;
        """
        cursor.execute(sql_resumo)
        print(f"   ✅ View criada: resumo_financeiro")
        
        # Criar view de transações por categoria
        sql_categoria = f"""
        CREATE OR REPLACE VIEW {schema_name}.transacoes_por_categoria AS 
        SELECT 
            cat.nome as categoria,
            cat.tipo as tipo_categoria,
            COUNT(t.id) as quantidade_transacoes,
            COALESCE(SUM(t.valor), 0) as valor_total
        FROM public.financas_categoria cat
        LEFT JOIN public.financas_transacao t ON cat.id = t.categoria_id AND t.tenant_id = {tenant.id}
        WHERE cat.tenant_id = {tenant.id}
        GROUP BY cat.id, cat.nome, cat.tipo
        ORDER BY valor_total DESC;
        """
        cursor.execute(sql_categoria)
        print(f"   ✅ View criada: transacoes_por_categoria")
        
        print(f"   🎉 Schema {schema_name} criado com sucesso!")
        return schema_name
        
    except Exception as e:
        print(f"   ❌ Erro ao criar schema para {user.username}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def criar_todos_schemas():
    """
    Cria schemas para todos os usuários.
    """
    print("🏗️  CRIANDO SCHEMAS VIRTUAIS POR USUÁRIO")
    print("="*60)
    
    schemas_criados = []
    
    # Para cada usuário/tenant
    for user in CustomUser.objects.all():
        # Obter tenant do usuário
        tenant = Tenant.objects.filter(usuarios=user).first()
        if not tenant:
            print(f"⚠️  Usuário {user.username} não tem tenant associado")
            continue
        
        schema_name = criar_schema_usuario(user, tenant)
        if schema_name:
            schemas_criados.append(schema_name)
    
    return schemas_criados

def demonstrar_uso(schemas_criados):
    """
    Demonstra como usar os schemas criados.
    """
    if not schemas_criados:
        print("\n⚠️  Nenhum schema foi criado.")
        return
    
    db_config = settings.DATABASES['default']
    
    print("\n" + "="*60)
    print("✅ SCHEMAS CRIADOS COM SUCESSO!")
    print(f"\n📋 SCHEMAS DISPONÍVEIS: {len(schemas_criados)}")
    for schema in schemas_criados:
        print(f"   • {schema}")
    
    print("\n🔍 COMO USAR NO POSTGRESQL:")
    print("\n1. Conectar ao banco:")
    print(f"   psql -h {db_config['HOST']} -U {db_config['USER']} -d {db_config['NAME']}")
    
    print("\n2. Listar todos os schemas de usuários:")
    print("   SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%';")
    
    if schemas_criados:
        exemplo_schema = schemas_criados[0]
        print(f"\n3. Exemplo com o schema '{exemplo_schema}':")
        print(f"   -- Ver todas as transações do usuário")
        print(f"   SELECT * FROM {exemplo_schema}.transacoes;")
        print(f"   ")
        print(f"   -- Ver resumo financeiro")
        print(f"   SELECT * FROM {exemplo_schema}.resumo_financeiro;")
        print(f"   ")
        print(f"   -- Ver transações por categoria")
        print(f"   SELECT * FROM {exemplo_schema}.transacoes_por_categoria;")
        print(f"   ")
        print(f"   -- Definir como schema padrão (opcional)")
        print(f"   SET search_path TO {exemplo_schema};")
        print(f"   SELECT * FROM transacoes;  -- Agora sem prefixo")
    
    print("\n💡 VANTAGENS:")
    print("   ✅ Consultas diretas no banco por usuário")
    print("   ✅ Isolamento automático dos dados")
    print("   ✅ Views pré-calculadas para relatórios")
    print("   ✅ Sistema Django continua funcionando normalmente")
    print("   ✅ Não altera nenhuma tabela existente")

def testar_schema_criado():
    """
    Testa se os schemas foram criados corretamente.
    """
    db_config = settings.DATABASES['default']
    conn = psycopg2.connect(
        host=db_config['HOST'],
        database=db_config['NAME'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        port=db_config['PORT']
    )
    
    cursor = conn.cursor()
    
    # Listar schemas de usuários
    cursor.execute("""
        SELECT 
            s.schema_name,
            COUNT(t.table_name) as total_views
        FROM information_schema.schemata s
        LEFT JOIN information_schema.views t ON s.schema_name = t.table_schema
        WHERE s.schema_name LIKE 'user_%'
        GROUP BY s.schema_name
        ORDER BY s.schema_name;
    """)
    
    schemas = cursor.fetchall()
    
    print("\n📊 TESTE DOS SCHEMAS CRIADOS:")
    print("-" * 50)
    
    if not schemas:
        print("   ⚠️  Nenhum schema de usuário encontrado.")
    else:
        for schema_name, view_count in schemas:
            print(f"   {schema_name:<25} | {view_count} views")
            
            # Testar uma consulta simples
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.transacoes;")
                count = cursor.fetchone()[0]
                print(f"   {' '*25} | {count} transações")
            except Exception as e:
                print(f"   {' '*25} | Erro: {e}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("🎯 CRIADOR DE SCHEMAS VIRTUAIS POR USUÁRIO - VERSÃO MELHORADA")
    print("\nEste script cria schemas separados para facilitar consultas")
    print("diretas no PostgreSQL, mantendo o sistema Django intacto.")
    
    try:
        schemas_criados = criar_todos_schemas()
        demonstrar_uso(schemas_criados)
        testar_schema_criado()
        
    except Exception as e:
        print(f"\n❌ Erro geral: {e}")
        print("\nVerifique se:")
        print("   • PostgreSQL está rodando")
        print("   • Credenciais estão corretas no .env")
        print("   • Usuário tem permissões para criar schemas")