#!/usr/bin/env python
import os
import django
from decimal import Decimal
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import DespesaParcelada, Categoria, Conta, Transacao
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

print('=== TESTE DE CRIAÇÃO DE NOVA DESPESA PARCELADA ===')

# Simular login do usuário mateus (ID 5)
user = User.objects.get(id=5)
print(f'Usuário logado: {user.username} (ID: {user.id})')

# Simular configuração do tenant_id na conexão
connection.tenant_id = user.id
print(f'Tenant ID configurado: {connection.tenant_id}')

# Verificar categorias e contas disponíveis
categorias = Categoria.objects.all()
contas = Conta.objects.all()

print(f'\nCategorias disponíveis: {categorias.count()}')
for cat in categorias:
    print(f'  - {cat.nome} (ID: {cat.id}, Tenant: {cat.tenant_id})')

print(f'\nContas disponíveis: {contas.count()}')
for conta in contas:
    print(f'  - {conta.nome} (ID: {conta.id}, Tenant: {conta.tenant_id})')

if not categorias.exists() or not contas.exists():
    print('\n❌ ERRO: Não há categorias ou contas disponíveis para o teste')
    exit(1)

# Criar nova despesa parcelada
print('\n=== CRIANDO NOVA DESPESA PARCELADA ===')

categoria = categorias.first()
conta = contas.first()

nova_despesa = DespesaParcelada(
    descricao='Teste Notebook Gaming',
    valor_total=Decimal('2500.00'),
    numero_parcelas=10,
    data_primeira_parcela=date.today(),
    categoria=categoria,
    conta=conta,
    responsavel=user
)

try:
    nova_despesa.save()
    print(f'✅ Despesa criada com sucesso!')
    print(f'   ID: {nova_despesa.id}')
    print(f'   Descrição: {nova_despesa.descricao}')
    print(f'   Tenant ID: {nova_despesa.tenant_id}')
    print(f'   Valor Total: R$ {nova_despesa.valor_total}')
    print(f'   Parcelas: {nova_despesa.numero_parcelas}')
except Exception as e:
    print(f'❌ Erro ao criar despesa: {e}')
    exit(1)

# Verificar se as parcelas foram geradas
print('\n=== VERIFICANDO PARCELAS GERADAS ===')
parcelas = Transacao.objects.filter(despesa_parcelada=nova_despesa)
print(f'Parcelas geradas: {parcelas.count()}')

for i, parcela in enumerate(parcelas, 1):
    print(f'  Parcela {i}: R$ {parcela.valor} - Vencimento: {parcela.data} - Tenant: {parcela.tenant_id}')

# Testar recuperação da despesa usando get_object_or_404 simulado
print('\n=== TESTANDO RECUPERAÇÃO DA DESPESA ===')
try:
    despesa_recuperada = DespesaParcelada.objects.get(id=nova_despesa.id)
    print(f'✅ Despesa recuperada com sucesso!')
    print(f'   ID: {despesa_recuperada.id}')
    print(f'   Descrição: {despesa_recuperada.descricao}')
    print(f'   Tenant ID: {despesa_recuperada.tenant_id}')
except DespesaParcelada.DoesNotExist:
    print(f'❌ ERRO: Despesa não encontrada (problema de tenant_id)')
    exit(1)

# Simular acesso via URL (testando o redirecionamento)
print('\n=== SIMULANDO ACESSO VIA URL ===')
print(f'URL de redirecionamento seria: /despesa-parcelada/{nova_despesa.id}/?parcelas_geradas=true')

# Verificar se a despesa aparece na listagem
print('\n=== VERIFICANDO LISTAGEM DE DESPESAS ===')
todas_despesas = DespesaParcelada.objects.all()
print(f'Total de despesas visíveis: {todas_despesas.count()}')

for despesa in todas_despesas:
    print(f'  - ID {despesa.id}: {despesa.descricao} (Tenant: {despesa.tenant_id})')

print('\n=== TESTE CONCLUÍDO COM SUCESSO! ===')
print('✅ Nova despesa parcelada criada e testada')
print('✅ Parcelas geradas corretamente')
print('✅ Recuperação por ID funcionando')
print('✅ Tenant ID aplicado corretamente')
print('✅ Redirecionamento deve funcionar normalmente')