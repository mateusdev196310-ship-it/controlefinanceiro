#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Debug: Verificar configuração do banco
echo "[BUILD] Verificando configuração do banco de dados..."
python manage.py shell -c "from django.conf import settings; print(f'Database Engine: {settings.DATABASES["default"]["ENGINE"]}'); print(f'Database Name: {settings.DATABASES["default"]["NAME"]}')"

# Verificar se há migrações pendentes
echo "[BUILD] Verificando migrações pendentes..."
python manage.py showmigrations

# Criar migrações se necessário
echo "[BUILD] Criando migrações..."
python manage.py makemigrations

# Run migrations
echo "[BUILD] Executando migrações..."
python manage.py migrate --verbosity=2

# Collect static files
echo "[BUILD] Coletando arquivos estáticos..."
python manage.py collectstatic --no-input