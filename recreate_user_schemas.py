import os
import django
import psycopg2
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser

def recreate_user_schemas():
    print("=== RECRIANDO SCHEMAS PARA USUÁRIOS ATIVOS ===")
    
    # Obter todos os usuários ativos
    users = CustomUser.objects.all()
    
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        
        cursor = conn.cursor()
        
        for user in users:
            schema_name = f"user_{user.id}"
            
            print(f"\nCriando schema para usuário ID {user.id} ({user.username})...")
            
            # Verificar se o schema já existe
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s;
            """, (schema_name,))
            
            if cursor.fetchone():
                print(f"  ✅ Schema {schema_name} já existe")
                continue
            
            # Criar o schema
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
            
            # Criar as tabelas no schema
            tables_sql = f"""
            -- Tabela de Bancos
            CREATE TABLE IF NOT EXISTS {schema_name}.financas_banco (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                codigo VARCHAR(10) UNIQUE NOT NULL
            );
            
            -- Tabela de Contas
            CREATE TABLE IF NOT EXISTS {schema_name}.financas_conta (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                saldo_inicial DECIMAL(10,2) DEFAULT 0.00,
                saldo_atual DECIMAL(10,2) DEFAULT 0.00,
                banco_id INTEGER REFERENCES {schema_name}.financas_banco(id) ON DELETE SET NULL,
                tenant_id INTEGER NOT NULL,
                cor VARCHAR(7) DEFAULT '#007bff'
            );
            
            -- Tabela de Categorias
            CREATE TABLE IF NOT EXISTS {schema_name}.financas_categoria (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('receita', 'despesa')),
                tenant_id INTEGER NOT NULL
            );
            
            -- Tabela de Transações
            CREATE TABLE IF NOT EXISTS {schema_name}.financas_transacao (
                id SERIAL PRIMARY KEY,
                descricao VARCHAR(200) NOT NULL,
                valor DECIMAL(10,2) NOT NULL,
                data DATE NOT NULL,
                tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('receita', 'despesa')),
                conta_id INTEGER NOT NULL REFERENCES {schema_name}.financas_conta(id) ON DELETE CASCADE,
                categoria_id INTEGER REFERENCES {schema_name}.financas_categoria(id) ON DELETE SET NULL,
                pago BOOLEAN DEFAULT FALSE,
                tenant_id INTEGER NOT NULL
            );
            
            -- Tabela de Despesas Parceladas
            CREATE TABLE IF NOT EXISTS {schema_name}.financas_despesaparcelada (
                id SERIAL PRIMARY KEY,
                descricao VARCHAR(200) NOT NULL,
                valor_total DECIMAL(10,2) NOT NULL,
                numero_parcelas INTEGER NOT NULL,
                data_primeira_parcela DATE NOT NULL,
                conta_id INTEGER NOT NULL REFERENCES {schema_name}.financas_conta(id) ON DELETE CASCADE,
                categoria_id INTEGER REFERENCES {schema_name}.financas_categoria(id) ON DELETE SET NULL,
                tenant_id INTEGER NOT NULL,
                responsavel VARCHAR(100)
            );
            
            -- Tabela de Fechamento Mensal
            CREATE TABLE IF NOT EXISTS {schema_name}.financas_fechamentomensal (
                id SERIAL PRIMARY KEY,
                mes INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                saldo_inicial DECIMAL(10,2) NOT NULL,
                total_receitas DECIMAL(10,2) NOT NULL,
                total_despesas DECIMAL(10,2) NOT NULL,
                saldo_final DECIMAL(10,2) NOT NULL,
                data_fechamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                conta_id INTEGER NOT NULL REFERENCES {schema_name}.financas_conta(id) ON DELETE CASCADE,
                tenant_id INTEGER NOT NULL,
                UNIQUE(mes, ano, conta_id)
            );
            
            -- Inserir bancos padrão
            INSERT INTO {schema_name}.financas_banco (nome, codigo) VALUES
                ('Banco do Brasil', '001'),
                ('Bradesco', '237'),
                ('Caixa Econômica Federal', '104'),
                ('Itaú', '341'),
                ('Santander', '033'),
                ('Nubank', '260'),
                ('Inter', '077'),
                ('C6 Bank', '336'),
                ('Banco Original', '212'),
                ('Banco Next', '237')
            ON CONFLICT (codigo) DO NOTHING;
            
            -- Inserir categorias padrão
            INSERT INTO {schema_name}.financas_categoria (nome, tipo, tenant_id) VALUES
                ('Salário', 'receita', {user.id}),
                ('Freelance', 'receita', {user.id}),
                ('Investimentos', 'receita', {user.id}),
                ('Alimentação', 'despesa', {user.id}),
                ('Transporte', 'despesa', {user.id}),
                ('Moradia', 'despesa', {user.id}),
                ('Saúde', 'despesa', {user.id}),
                ('Educação', 'despesa', {user.id}),
                ('Lazer', 'despesa', {user.id}),
                ('Outros', 'despesa', {user.id})
            ON CONFLICT DO NOTHING;
            """
            
            # Executar as queries
            cursor.execute(tables_sql)
            
            print(f"  ✅ Schema {schema_name} criado com sucesso")
        
        # Commit das mudanças
        conn.commit()
        
        print(f"\n=== RESUMO ===")
        print(f"Schemas recriados para {users.count()} usuários ativos")
        print("Todos os usuários agora têm seus schemas correspondentes")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao recriar schemas: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    recreate_user_schemas()