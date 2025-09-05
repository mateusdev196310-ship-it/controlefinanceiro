#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.contrib.auth import get_user_model
from financas.models import Categoria, Conta, Banco

User = get_user_model()

print("=== Criando dados de teste para usuário testuser (ID: 7) ===")

# Encontrar o usuário testuser
try:
    user = User.objects.get(username='testuser')
    print(f"Usuário encontrado: {user.username} (ID: {user.id})")
except User.DoesNotExist:
    print("Usuário testuser não encontrado!")
    exit(1)

tenant_id = user.id  # Usar ID do usuário como tenant_id

# Criar categorias para o tenant_id 7
print(f"\nCriando categorias para tenant_id {tenant_id}...")

categorias_data = [
    {'nome': 'Alimentação', 'cor': '#ff6b6b', 'tipo': 'despesa'},
    {'nome': 'Transporte', 'cor': '#4ecdc4', 'tipo': 'despesa'},
    {'nome': 'Salário', 'cor': '#45b7d1', 'tipo': 'receita'},
]

for cat_data in categorias_data:
    categoria, created = Categoria.objects.get_or_create(
        nome=cat_data['nome'],
        tenant_id=tenant_id,
        defaults={
            'cor': cat_data['cor'],
            'tipo': cat_data['tipo']
        }
    )
    if created:
        print(f"  ✓ Categoria criada: {categoria.nome} (ID: {categoria.id})")
    else:
        print(f"  - Categoria já existe: {categoria.nome} (ID: {categoria.id})")

# Criar banco se não existir
print(f"\nCriando banco...")
banco, created = Banco.objects.get_or_create(
    codigo='001',
    defaults={'nome': 'Banco do Brasil'}
)
if created:
    print(f"  ✓ Banco criado: {banco.nome}")
else:
    print(f"  - Banco já existe: {banco.nome}")

# Criar contas para o tenant_id 7
print(f"\nCriando contas para tenant_id {tenant_id}...")

contas_data = [
    {'nome': 'Conta Corrente Principal', 'tipo': 'bancaria', 'saldo': '1000.00'},
    {'nome': 'Carteira', 'tipo': 'simples', 'saldo': '200.00'},
]

for conta_data in contas_data:
    conta, created = Conta.objects.get_or_create(
        nome=conta_data['nome'],
        tenant_id=tenant_id,
        defaults={
            'tipo': conta_data['tipo'],
            'saldo': conta_data['saldo'],
            'banco': banco if conta_data['tipo'] == 'bancaria' else None
        }
    )
    if created:
        print(f"  ✓ Conta criada: {conta.nome} (ID: {conta.id})")
    else:
        print(f"  - Conta já existe: {conta.nome} (ID: {conta.id})")

# Listar dados criados
print(f"\n=== Dados disponíveis para tenant_id {tenant_id} ===")

print("\nCategorias:")
categorias = Categoria.objects.filter(tenant_id=tenant_id)
for cat in categorias:
    print(f"  - {cat.nome} (ID: {cat.id}, Tipo: {cat.tipo})")

print("\nContas:")
contas = Conta.objects.filter(tenant_id=tenant_id)
for conta in contas:
    print(f"  - {conta.nome} (ID: {conta.id}, Saldo: R$ {conta.saldo})")

print("\n=== Dados criados com sucesso! ===")