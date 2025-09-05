#!/usr/bin/env python
import os
import django
from datetime import datetime, date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Transacao, Categoria, Conta
from django.utils import timezone

print("=== DEBUG: Análise de Datas das Transações ===")
print(f"Data atual do sistema: {timezone.now().date()}")
print(f"Data atual Python: {date.today()}")
print()

# Verificar todas as transações e suas datas
transacoes = Transacao.objects.all().order_by('-data')
print(f"Total de transações: {transacoes.count()}")
print()

print("=== Transações por Data ===")
for transacao in transacoes:
    print(f"ID: {transacao.id} | Data: {transacao.data} | Tipo: {transacao.tipo} | Descrição: {transacao.descricao} | Valor: R$ {transacao.valor}")

print()
print("=== Análise de Datas ===")
hoje = date.today()
futuras = transacoes.filter(data__gt=hoje)
passadas = transacoes.filter(data__lte=hoje)

print(f"Transações com data futura (após {hoje}): {futuras.count()}")
for t in futuras:
    print(f"  - {t.data}: {t.descricao} (R$ {t.valor})")

print(f"\nTransações com data atual ou passada: {passadas.count()}")
for t in passadas:
    print(f"  - {t.data}: {t.descricao} (R$ {t.valor})")

print()
print("=== Teste de Template Tag 'now' ===")
from django.template import Context, Template
template = Template("{% now 'Y-m-d' %}")
context = Context({})
data_template = template.render(context)
print(f"Template {{% now 'Y-m-d' %}} retorna: {data_template}")
print(f"Isso corresponde à data atual? {data_template == str(date.today())}")

print()
print("=== Verificação de Timezone ===")
print(f"timezone.now(): {timezone.now()}")
print(f"timezone.now().date(): {timezone.now().date()}")
print(f"Timezone configurado: {timezone.get_current_timezone()}")