#!/usr/bin/env python
import os
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.contrib.auth import get_user_model
from financas.models import Categoria
from financas.middleware import TenantMiddleware
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

User = get_user_model()

print("=== Debug Tenant Category Issue ===")

# Encontrar o usuário testuser
try:
    user = User.objects.get(username='testuser')
    print(f"Usuário encontrado: {user.username} (ID: {user.id})")
    print(f"CPF: {user.cpf}")
    print(f"CNPJ: {user.cnpj}")
    print(f"Schema name: {user.schema_name}")
    print(f"Tipo pessoa: {user.tipo_pessoa}")
except User.DoesNotExist:
    print("Usuário testuser não encontrado!")
    exit(1)

# Verificar schema atual
print(f"\nSchema atual: {connection.schema_name if hasattr(connection, 'schema_name') else 'Não definido'}")

# Simular middleware de tenant
factory = RequestFactory()
request = factory.post('/adicionar-despesa-parcelada/')
request.user = user

# Aplicar middleware de sessão
session_middleware = SessionMiddleware(lambda req: None)
session_middleware.process_request(request)
request.session.save()

# Aplicar middleware de autenticação
auth_middleware = AuthenticationMiddleware(lambda req: None)
auth_middleware.process_request(request)

# Aplicar middleware de tenant
tenant_middleware = TenantMiddleware(lambda req: None)
tenant_middleware.process_request(request)

print(f"Schema após middleware: {connection.schema_name if hasattr(connection, 'schema_name') else 'Não definido'}")

# Tentar buscar categorias
print("\n=== Buscando Categorias ===")
try:
    categorias = Categoria.objects.all()
    print(f"Total de categorias encontradas: {categorias.count()}")
    for cat in categorias:
        print(f"  - {cat.nome} (ID: {cat.id}, Tenant: {cat.tenant_id})")
except Exception as e:
    print(f"Erro ao buscar categorias: {e}")

# Tentar buscar categoria específica (ID 9)
print("\n=== Buscando Categoria ID 9 ===")
try:
    categoria = Categoria.objects.get(id=9)
    print(f"Categoria encontrada: {categoria.nome} (Tenant: {categoria.tenant_id})")
except Categoria.DoesNotExist:
    print("Categoria ID 9 não encontrada no schema atual!")
except Exception as e:
    print(f"Erro ao buscar categoria ID 9: {e}")

# Verificar se existe categoria com tenant_id correto
print("\n=== Buscando Categorias por Tenant ID ===")
try:
    # Usar o ID do usuário como tenant_id
    categorias_tenant = Categoria.objects.filter(tenant_id=user.id)
    print(f"Categorias para tenant_id {user.id}: {categorias_tenant.count()}")
    for cat in categorias_tenant:
        print(f"  - {cat.nome} (ID: {cat.id})")
except Exception as e:
    print(f"Erro ao buscar categorias por tenant: {e}")

print("\n=== Debug concluído ===")