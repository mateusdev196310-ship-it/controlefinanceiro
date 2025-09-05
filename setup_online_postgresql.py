#!/usr/bin/env python3
"""
Script para configurar PostgreSQL online gratuito
Opções: ElephantSQL, Supabase, ou Neon
"""

import os
import requests
import json
from urllib.parse import urlparse

def setup_elephantsql():
    """
    Configurar ElephantSQL (PostgreSQL gratuito)
    """
    print("\n=== Configuração ElephantSQL ===")
    print("1. Acesse: https://www.elephantsql.com/")
    print("2. Clique em 'Get a managed database today'")
    print("3. Crie uma conta gratuita")
    print("4. Crie uma nova instância:")
    print("   - Name: financeiro-db")
    print("   - Plan: Tiny Turtle (Free)")
    print("   - Region: Escolha a mais próxima")
    print("5. Após criar, copie a URL de conexão")
    print("6. Cole a URL quando solicitado")
    
    url = input("\nCole a URL de conexão do ElephantSQL: ").strip()
    
    if url:
        return parse_database_url(url)
    return None

def setup_supabase():
    """
    Configurar Supabase (PostgreSQL gratuito)
    """
    print("\n=== Configuração Supabase ===")
    print("1. Acesse: https://supabase.com/")
    print("2. Clique em 'Start your project'")
    print("3. Crie uma conta gratuita")
    print("4. Crie um novo projeto:")
    print("   - Name: financeiro")
    print("   - Database Password: (anote a senha)")
    print("   - Region: Escolha a mais próxima")
    print("5. Vá em Settings > Database")
    print("6. Copie a Connection String (URI)")
    
    url = input("\nCole a Connection String do Supabase: ").strip()
    
    if url:
        return parse_database_url(url)
    return None

def setup_neon():
    """
    Configurar Neon (PostgreSQL gratuito)
    """
    print("\n=== Configuração Neon ===")
    print("1. Acesse: https://neon.tech/")
    print("2. Clique em 'Sign up'")
    print("3. Crie uma conta gratuita")
    print("4. Crie um novo projeto:")
    print("   - Project name: financeiro")
    print("   - Database name: financeiro_db")
    print("5. Copie a connection string")
    
    url = input("\nCole a Connection String do Neon: ").strip()
    
    if url:
        return parse_database_url(url)
    return None

def parse_database_url(url):
    """
    Parse da URL do banco de dados
    """
    try:
        parsed = urlparse(url)
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed.path[1:],  # Remove a barra inicial
            'USER': parsed.username,
            'PASSWORD': parsed.password,
            'HOST': parsed.hostname,
            'PORT': parsed.port or 5432,
        }
    except Exception as e:
        print(f"Erro ao fazer parse da URL: {e}")
        return None

def update_env_file(db_config):
    """
    Atualizar arquivo .env com as configurações do banco
    """
    env_content = f"""# Configurações do Banco de Dados PostgreSQL Online
DB_ENGINE={db_config['ENGINE']}
DB_NAME={db_config['NAME']}
DB_USER={db_config['USER']}
DB_PASSWORD={db_config['PASSWORD']}
DB_HOST={db_config['HOST']}
DB_PORT={db_config['PORT']}

# Usar PostgreSQL online
USE_SQLITE=False

# Configurações Django
SECRET_KEY=django-insecure-q3i&$4h-)gesath0@4oo660!y3=or_8ss_w0j%#l211^5tz+7-
DEBUG=True
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("\n✅ Arquivo .env atualizado com sucesso!")

def main():
    print("🐘 Configurador de PostgreSQL Online Gratuito")
    print("="*50)
    
    print("\nEscolha um provedor:")
    print("1. ElephantSQL (Recomendado)")
    print("2. Supabase")
    print("3. Neon")
    print("4. Configuração manual")
    
    choice = input("\nDigite sua escolha (1-4): ").strip()
    
    db_config = None
    
    if choice == '1':
        db_config = setup_elephantsql()
    elif choice == '2':
        db_config = setup_supabase()
    elif choice == '3':
        db_config = setup_neon()
    elif choice == '4':
        print("\n=== Configuração Manual ===")
        db_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': input("Database Name: ").strip(),
            'USER': input("Username: ").strip(),
            'PASSWORD': input("Password: ").strip(),
            'HOST': input("Host: ").strip(),
            'PORT': input("Port (5432): ").strip() or '5432',
        }
    else:
        print("Opção inválida!")
        return
    
    if db_config:
        update_env_file(db_config)
        print("\n🎉 Configuração concluída!")
        print("\nPróximos passos:")
        print("1. Execute: python manage.py makemigrations")
        print("2. Execute: python manage.py migrate")
        print("3. Execute: python manage.py createsuperuser")
    else:
        print("\n❌ Configuração cancelada.")

if __name__ == '__main__':
    main()