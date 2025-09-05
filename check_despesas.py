#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import DespesaParcelada

print('=== Despesas Parceladas Existentes ===')
despesas = DespesaParcelada.objects.all()
print(f'Total de despesas encontradas: {despesas.count()}')

for d in despesas:
    print(f'ID: {d.id}, Descrição: {d.descricao}, Tenant ID: {d.tenant_id}')

print('\n=== Verificando Despesa ID 9 ===')
try:
    despesa_9 = DespesaParcelada.objects.get(id=9)
    print(f'Despesa ID 9 encontrada: {despesa_9.descricao}, Tenant ID: {despesa_9.tenant_id}')
except DespesaParcelada.DoesNotExist:
    print('Despesa ID 9 não existe no banco de dados')

print('\n=== Verificando com filtro de tenant_id ===')
from django.db import connection
print(f'Tenant ID atual na conexão: {getattr(connection, "tenant_id", "Não definido")}')

# Verificar se existe despesa 9 sem filtro de tenant
from django.db import models
class DespesaParceladaSemTenant(models.Model):
    class Meta:
        db_table = 'financas_despesaparcelada'
        managed = False
    
    id = models.AutoField(primary_key=True)
    descricao = models.CharField(max_length=200)
    tenant_id = models.IntegerField(null=True)

try:
    despesa_9_raw = DespesaParceladaSemTenant.objects.get(id=9)
    print(f'Despesa ID 9 (sem filtro tenant): Descrição: {despesa_9_raw.descricao}, Tenant ID: {despesa_9_raw.tenant_id}')
except DespesaParceladaSemTenant.DoesNotExist:
    print('Despesa ID 9 não existe no banco (consulta raw)')