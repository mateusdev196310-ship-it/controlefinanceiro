#!/usr/bin/env python
"""
Script para criar schemas virtuais por usuário no PostgreSQL
Isso facilita consultas diretas no banco sem alterar o sistema Django.

Cada usuário terá um schema com seu CPF/CNPJ contendo views das suas tabelas.
"""

import os
import django
import psycopg2
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser, Tenant

def criar_schemas_usuarios():
    """
    Cria schemas separados para cada usuário com views filtradas.
    """
    
    # Conectar ao PostgreSQL
    db_config = settings.DATABASES['default']
    conn = psycopg2.connect(
        host=db_config['HOST'],
        database=db_config['NAME'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        port=db_config['PORT']
    )
    
    cursor = conn.cursor()
    
    print("🏗️  CRIANDO SCHEMAS VIRTUAIS POR USUÁRIO")
    print("="*50)
    
    # Para cada usuário/tenant
    for user in CustomUser.objects.all():
        try:
            # Obter tenant do usuário
            tenant = Tenant.objects.filter(usuarios=user).first()
            if not tenant:
                print(f"⚠️  Usuário {user.username} não tem tenant associado")
                continue
                
            # Nome do schema baseado no CPF/CNPJ
            if user.cpf:
                schema_name = f"user_{user.cpf.replace('.', '').replace('-', '')}"
            elif user.cnpj:
                schema_name = f"user_{user.cnpj.replace('.', '').replace('/', '').replace('-', '')}"
            else:
                schema_name = f"user_{user.username}"
            
            print(f"\n👤 Criando schema para: {user.username} ({schema_name})")
            
            # Criar schema
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
            
            # Criar views filtradas por tenant_id
            views = [
                ('transacoes', 'financas_transacao', tenant.id),
                ('contas', 'financas_conta', tenant.id),
                ('categorias', 'financas_categoria', tenant.id),
                ('despesas_parceladas', 'financas_despesaparcelada', tenant.id)
            ]
            
            for view_name, table_name, tenant_id in views:
                sql = f"""
                CREATE OR REPLACE VIEW {schema_name}.{view_name} AS 
                SELECT * FROM public.{table_name} 
                WHERE tenant_id = {tenant_id};
                """
                cursor.execute(sql)
                print(f"   ✅ View criada: {schema_name}.{view_name}")
            
            # Criar view de resumo financeiro
            sql_resumo = f"""
            CREATE OR REPLACE VIEW {schema_name}.resumo_financeiro AS 
            SELECT 
                c.nome as conta,
                c.saldo,
                COUNT(t.id) as total_transacoes,
                SUM(CASE WHEN t.tipo = 'receita' THEN t.valor ELSE 0 END) as total_receitas,
                SUM(CASE WHEN t.tipo = 'despesa' THEN t.valor ELSE 0 END) as total_despesas
            FROM public.financas_conta c
            LEFT JOIN public.financas_transacao t ON c.id = t.conta_id AND t.tenant_id = {tenant.id}
            WHERE c.tenant_id = {tenant.id}
            GROUP BY c.id, c.nome, c.saldo;
            """
            cursor.execute(sql_resumo)
            print(f"   ✅ View criada: {schema_name}.resumo_financeiro")
            
            # Dar permissões ao usuário (se existir no PostgreSQL)
            try:
                cursor.execute(f"GRANT USAGE ON SCHEMA {schema_name} TO {user.username};")
                cursor.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema_name} TO {user.username};")
                print(f"   ✅ Permissões concedidas para {user.username}")
            except:
                print(f"   ⚠️  Usuário {user.username} não existe no PostgreSQL")
                
        except Exception as e:
            print(f"   ❌ Erro ao criar schema para {user.username}: {e}")
    
    # Commit das alterações
    conn.commit()
    
    print("\n" + "="*50)
    print("✅ SCHEMAS CRIADOS COM SUCESSO!")
    print("\n📋 COMO USAR:")
    print("\n1. Conecte no PostgreSQL:")
    print(f"   psql -h {db_config['HOST']} -U {db_config['USER']} -d {db_config['NAME']}")
    print("\n2. Liste os schemas:")
    print("   \\dn")
    print("\n3. Consulte dados de um usuário específico:")
    print("   SELECT * FROM user_12345678901.transacoes;")
    print("   SELECT * FROM user_12345678901.resumo_financeiro;")
    print("\n4. Mude para o schema do usuário:")
    print("   SET search_path TO user_12345678901;")
    print("   SELECT * FROM transacoes;  -- Agora sem prefixo")
    
    # Listar schemas criados
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE 'user_%'
        ORDER BY schema_name;
    """)
    
    schemas = cursor.fetchall()
    if schemas:
        print("\n🏗️  SCHEMAS CRIADOS:")
        for schema in schemas:
            print(f"   • {schema[0]}")
    
    cursor.close()
    conn.close()

def listar_schemas_existentes():
    """
    Lista schemas de usuários já criados.
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
    
    cursor.execute("""
        SELECT 
            s.schema_name,
            COUNT(t.table_name) as total_views
        FROM information_schema.schemata s
        LEFT JOIN information_schema.tables t ON s.schema_name = t.table_schema
        WHERE s.schema_name LIKE 'user_%'
        GROUP BY s.schema_name
        ORDER BY s.schema_name;
    """)
    
    schemas = cursor.fetchall()
    
    print("\n📊 SCHEMAS DE USUÁRIOS EXISTENTES:")
    print("-" * 40)
    for schema_name, view_count in schemas:
        print(f"   {schema_name:<25} | {view_count} views")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("🎯 CRIADOR DE SCHEMAS VIRTUAIS POR USUÁRIO")
    print("\nEste script cria schemas separados para cada usuário")
    print("facilitando consultas diretas no PostgreSQL.")
    print("\nO sistema Django continua funcionando normalmente!")
    
    resposta = input("\nDeseja continuar? (s/n): ")
    if resposta.lower() == 's':
        try:
            listar_schemas_existentes()
            criar_schemas_usuarios()
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            print("\nVerifique se o PostgreSQL está rodando e as credenciais estão corretas.")
    else:
        print("\n👋 Operação cancelada.")