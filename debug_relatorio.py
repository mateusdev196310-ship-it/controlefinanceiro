#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Transacao, Categoria
from datetime import datetime
from django.db.models import Sum, Q

print('=== ANÁLISE DO PROBLEMA NO RELATÓRIO GERAL ===')
print('Data atual:', datetime.now().date())
print()

# Verificar todas as transações
print('TODAS AS TRANSAÇÕES:')
for t in Transacao.objects.all().order_by('data'):
    parcelada = 'SIM' if t.despesa_parcelada is not None else 'NÃO'
    print(f'ID: {t.id}, Tipo: {t.tipo}, Valor: R$ {t.valor}, Data: {t.data}, Categoria: {t.categoria}, Parcelada: {parcelada}')

print('\n' + '='*50)
print('RESUMO POR TIPO:')
print(f'Total de transações: {Transacao.objects.count()}')
print(f'Receitas: {Transacao.objects.filter(tipo="receita").count()}')
print(f'Despesas: {Transacao.objects.filter(tipo="despesa").count()}')
print(f'Despesas parceladas: {Transacao.objects.filter(despesa_parcelada__isnull=False).count()}')

print('\n' + '='*50)
print('VALORES TOTAIS:')
receitas_total = Transacao.objects.filter(tipo='receita').aggregate(total=Sum('valor'))['total'] or 0
despesas_total = Transacao.objects.filter(tipo='despesa').aggregate(total=Sum('valor'))['total'] or 0
print(f'Total receitas: R$ {receitas_total}')
print(f'Total despesas: R$ {despesas_total}')
print(f'Saldo: R$ {receitas_total - despesas_total}')

print('\n' + '='*50)
print('CATEGORIAS:')
for c in Categoria.objects.all():
    tipo_categoria = getattr(c, 'tipo', 'N/A')
    print(f'ID: {c.id}, Nome: {c.nome}, Tipo: {tipo_categoria}')

print('\n' + '='*50)
print('TRANSAÇÕES POR CATEGORIA (DESPESAS):')
for categoria in Categoria.objects.all():
    total_categoria = Transacao.objects.filter(
        categoria=categoria, 
        tipo='despesa'
    ).aggregate(total=Sum('valor'))['total']
    
    if total_categoria:
        print(f'Categoria: {categoria.nome}, Total: R$ {total_categoria}')

print('\n' + '='*50)
print('VERIFICANDO FILTROS DO RELATÓRIO (MÊS ATUAL):')
hoje = datetime.now().date()
data_inicio = hoje.replace(day=1)
data_fim = hoje

filtro_periodo = Q(data__gte=data_inicio, data__lte=data_fim)
print(f'Período: {data_inicio} até {data_fim}')

receitas_mes = Transacao.objects.filter(tipo='receita').filter(filtro_periodo).aggregate(total=Sum('valor'))['total'] or 0
despesas_mes = Transacao.objects.filter(tipo='despesa').filter(filtro_periodo).aggregate(total=Sum('valor'))['total'] or 0

print(f'Receitas no período: R$ {receitas_mes}')
print(f'Despesas no período: R$ {despesas_mes}')
print(f'Saldo no período: R$ {receitas_mes - despesas_mes}')

print('\nTransações no período:')
for t in Transacao.objects.filter(filtro_periodo).order_by('data'):
    parcelada = 'SIM' if t.despesa_parcelada is not None else 'NÃO'
    print(f'  {t.data}: {t.tipo} - R$ {t.valor} - {t.categoria} - Parcelada: {parcelada}')

print('\n' + '='*50)
print('DESPESAS POR CATEGORIA NO PERÍODO:')
for categoria in Categoria.objects.all():
    total_categoria = Transacao.objects.filter(
        categoria=categoria, 
        tipo='despesa'
    ).filter(filtro_periodo).aggregate(total=Sum('valor'))['total']
    
    if total_categoria:
        print(f'  {categoria.nome}: R$ {total_categoria}')
    else:
        print(f'  {categoria.nome}: R$ 0,00')

print('\nFIM DA ANÁLISE')