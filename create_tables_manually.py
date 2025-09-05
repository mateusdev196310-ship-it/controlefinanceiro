import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def create_tables_manually():
    try:
        cursor = connection.cursor()
        
        # Criar tabela CustomUser
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_user_custom (
                id SERIAL PRIMARY KEY,
                password VARCHAR(128) NOT NULL,
                last_login TIMESTAMP WITH TIME ZONE,
                is_superuser BOOLEAN NOT NULL,
                username VARCHAR(150) NOT NULL UNIQUE,
                first_name VARCHAR(150) NOT NULL,
                last_name VARCHAR(150) NOT NULL,
                email VARCHAR(254) NOT NULL,
                is_staff BOOLEAN NOT NULL,
                is_active BOOLEAN NOT NULL,
                date_joined TIMESTAMP WITH TIME ZONE NOT NULL,
                tipo_pessoa VARCHAR(10) NOT NULL,
                cpf VARCHAR(14),
                cnpj VARCHAR(18)
            );
        """)
        print("✅ Tabela auth_user_custom criada")
        
        # Criar tabelas de relacionamento do CustomUser
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_user_custom_groups (
                id SERIAL PRIMARY KEY,
                customuser_id INTEGER NOT NULL REFERENCES auth_user_custom(id) DEFERRABLE INITIALLY DEFERRED,
                group_id INTEGER NOT NULL REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED,
                UNIQUE (customuser_id, group_id)
            );
        """)
        print("✅ Tabela auth_user_custom_groups criada")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_user_custom_user_permissions (
                id SERIAL PRIMARY KEY,
                customuser_id INTEGER NOT NULL REFERENCES auth_user_custom(id) DEFERRABLE INITIALLY DEFERRED,
                permission_id INTEGER NOT NULL REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED,
                UNIQUE (customuser_id, permission_id)
            );
        """)
        print("✅ Tabela auth_user_custom_user_permissions criada")
        
        # Criar tabela Tenant
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financas_tenant (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """)
        print("✅ Tabela financas_tenant criada")
        
        # Criar tabela de relacionamento Tenant-Usuario
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financas_tenant_usuarios (
                id SERIAL PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES financas_tenant(id) DEFERRABLE INITIALLY DEFERRED,
                customuser_id INTEGER NOT NULL REFERENCES auth_user_custom(id) DEFERRABLE INITIALLY DEFERRED,
                UNIQUE (tenant_id, customuser_id)
            );
        """)
        print("✅ Tabela financas_tenant_usuarios criada")
        
        # Criar tabela Banco
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financas_banco (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                codigo VARCHAR(10) NOT NULL UNIQUE
            );
        """)
        print("✅ Tabela financas_banco criada")
        
        # Criar tabela Categoria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financas_categoria (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                cor VARCHAR(7) NOT NULL,
                tenant_id INTEGER REFERENCES financas_tenant(id) DEFERRABLE INITIALLY DEFERRED
            );
        """)
        print("✅ Tabela financas_categoria criada")
        
        # Criar tabela Conta
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financas_conta (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                saldo DECIMAL(10, 2) NOT NULL,
                banco_id INTEGER NOT NULL REFERENCES financas_banco(id) DEFERRABLE INITIALLY DEFERRED,
                cor VARCHAR(7) NOT NULL,
                tipo VARCHAR(20) NOT NULL,
                tenant_id INTEGER REFERENCES financas_tenant(id) DEFERRABLE INITIALLY DEFERRED
            );
        """)
        print("✅ Tabela financas_conta criada")
        
        # Criar tabela Transacao
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financas_transacao (
                id SERIAL PRIMARY KEY,
                descricao VARCHAR(200) NOT NULL,
                valor DECIMAL(10, 2) NOT NULL,
                data DATE NOT NULL,
                tipo VARCHAR(10) NOT NULL,
                conta_id INTEGER NOT NULL REFERENCES financas_conta(id) DEFERRABLE INITIALLY DEFERRED,
                categoria_id INTEGER REFERENCES financas_categoria(id) DEFERRABLE INITIALLY DEFERRED,
                tenant_id INTEGER REFERENCES financas_tenant(id) DEFERRABLE INITIALLY DEFERRED
            );
        """)
        print("✅ Tabela financas_transacao criada")
        
        # Criar tabela DespesaParcelada
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financas_despesaparcelada (
                id SERIAL PRIMARY KEY,
                descricao VARCHAR(200) NOT NULL,
                valor_total DECIMAL(10, 2) NOT NULL,
                numero_parcelas INTEGER NOT NULL,
                data_inicio DATE NOT NULL,
                conta_id INTEGER NOT NULL REFERENCES financas_conta(id) DEFERRABLE INITIALLY DEFERRED,
                categoria_id INTEGER REFERENCES financas_categoria(id) DEFERRABLE INITIALLY DEFERRED,
                tenant_id INTEGER REFERENCES financas_tenant(id) DEFERRABLE INITIALLY DEFERRED
            );
        """)
        print("✅ Tabela financas_despesaparcelada criada")
        
        # Criar outras tabelas do sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financas_meta (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                valor_objetivo DECIMAL(10, 2) NOT NULL,
                valor_atual DECIMAL(10, 2) NOT NULL,
                data_limite DATE NOT NULL,
                categoria_id INTEGER REFERENCES financas_categoria(id) DEFERRABLE INITIALLY DEFERRED
            );
        """)
        print("✅ Tabela financas_meta criada")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financas_configuracaofechamento (
                id SERIAL PRIMARY KEY,
                dia_fechamento INTEGER NOT NULL,
                ativo BOOLEAN NOT NULL
            );
        """)
        print("✅ Tabela financas_configuracaofechamento criada")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financas_fechamentomensal (
                id SERIAL PRIMARY KEY,
                mes INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                saldo_inicial DECIMAL(10, 2) NOT NULL,
                saldo_final DECIMAL(10, 2) NOT NULL,
                total_receitas DECIMAL(10, 2) NOT NULL,
                total_despesas DECIMAL(10, 2) NOT NULL,
                data_fechamento TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """)
        print("✅ Tabela financas_fechamentomensal criada")
        
        print("\n🎉 Todas as tabelas foram criadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    create_tables_manually()