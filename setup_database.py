#!/usr/bin/env python
"""
Script para configurar o banco de dados (PostgreSQL ou SQLite como fallback)
"""

import os
import sys
import django
from pathlib import Path

# Adicionar o diretório do projeto ao Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from django.conf import settings

def test_postgresql_connection():
    """Testa se é possível conectar ao PostgreSQL"""
    try:
        # Tentar importar psycopg2
        import psycopg2
        
        # Tentar conectar ao PostgreSQL
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database='postgres'  # Conectar ao banco padrão primeiro
        )
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        return False

def create_postgresql_database():
    """Cria o banco de dados PostgreSQL se não existir"""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Conectar ao PostgreSQL como superusuário
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Verificar se o banco já existe
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", 
                      (settings.DATABASES['default']['NAME'],))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {settings.DATABASES['default']['NAME']}")
            print(f"Banco de dados '{settings.DATABASES['default']['NAME']}' criado com sucesso!")
        else:
            print(f"Banco de dados '{settings.DATABASES['default']['NAME']}' já existe.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao criar banco PostgreSQL: {e}")
        return False

def setup_sqlite_fallback():
    """Configura SQLite como fallback"""
    print("Configurando SQLite como banco de dados...")
    
    # Criar arquivo .env com USE_SQLITE=True
    env_content = """
# Configurações do Banco de Dados - Usando SQLite como fallback
USE_SQLITE=True

# Configurações Django
SECRET_KEY=django-insecure-q3i&$4h-)gesath0@4oo660!y3=or_8ss_w0j%#l211^5tz+7-
DEBUG=True
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("Configuração SQLite ativada no arquivo .env")

def run_migrations():
    """Executa as migrações do Django"""
    print("Executando migrações...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("Migrações executadas com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao executar migrações: {e}")
        return False

def main():
    print("=== Configuração do Banco de Dados ===")
    
    # Tentar PostgreSQL primeiro
    if test_postgresql_connection():
        print("PostgreSQL detectado! Configurando...")
        
        if create_postgresql_database():
            print("Usando PostgreSQL como banco de dados.")
        else:
            print("Falha ao configurar PostgreSQL. Usando SQLite como fallback.")
            setup_sqlite_fallback()
    else:
        print("PostgreSQL não disponível. Usando SQLite como fallback.")
        setup_sqlite_fallback()
    
    # Executar migrações
    if run_migrations():
        print("\n✅ Configuração do banco de dados concluída com sucesso!")
        
        # Testar conexão final
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            db_engine = settings.DATABASES['default']['ENGINE']
            if 'postgresql' in db_engine:
                print("🐘 Usando PostgreSQL")
            else:
                print("📁 Usando SQLite")
        except Exception as e:
            print(f"⚠️  Aviso: Erro ao testar conexão final: {e}")
    else:
        print("❌ Falha na configuração do banco de dados.")
        sys.exit(1)

if __name__ == '__main__':
    main()