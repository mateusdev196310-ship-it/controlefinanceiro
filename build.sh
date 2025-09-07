#!/usr/bin/env bash
# exit on error
set -o errexit

# Debug: Verificar configuração do banco
echo "=== DEBUG: Configuração do Banco ==="
echo "USE_SQLITE: $USE_SQLITE"
echo "DATABASE_URL: $DATABASE_URL"
echo "Python version: $(python --version)"
echo "Django version: $(python -c 'import django; print(django.get_version())')"
echo "======================================"

# Instalar dependências
pip install -r requirements.txt

# Debug: Verificar se o banco existe e tem tabelas
echo "=== DEBUG: Verificando banco de dados ==="
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table';\")
        tables = cursor.fetchall()
        print(f'Tabelas existentes: {[table[0] for table in tables]}')
        if 'auth_user_custom' in [table[0] for table in tables]:
            print('✓ Tabela auth_user_custom encontrada')
        else:
            print('✗ Tabela auth_user_custom NÃO encontrada')
except Exception as e:
    print(f'Erro ao verificar banco: {e}')
"
echo "============================================"

# Debug: Verificar migrações pendentes
echo "=== DEBUG: Verificando migrações ==="
python manage.py showmigrations
echo "===================================="

# Criar migrações se necessário
echo "=== Criando migrações se necessário ==="
python manage.py makemigrations --check || python manage.py makemigrations
echo "======================================"

# Executar migrações com verbosidade máxima
echo "=== Executando migrações ==="
python manage.py migrate --verbosity=3
echo "============================="

# Verificar novamente se as tabelas foram criadas
echo "=== DEBUG: Verificando tabelas após migração ==="
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table';\")
        tables = cursor.fetchall()
        print(f'Tabelas após migração: {[table[0] for table in tables]}')
        if 'auth_user_custom' in [table[0] for table in tables]:
            print('✓ Tabela auth_user_custom criada com sucesso')
        else:
            print('✗ ERRO: Tabela auth_user_custom ainda não existe!')
            exit(1)
except Exception as e:
    print(f'Erro ao verificar banco após migração: {e}')
    exit(1)
"
echo "==============================================="

# Coletar arquivos estáticos
echo "=== Coletando arquivos estáticos ==="
python manage.py collectstatic --no-input
echo "===================================="