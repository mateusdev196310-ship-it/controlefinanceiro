#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import DespesaParcelada, Categoria, Conta
from financas.utils import parse_currency_value
from django.db import connection
from decimal import Decimal
from datetime import date

# Definir tenant_id
connection.tenant_id = 5

print("=== SIMULANDO CRIAÇÃO DE DESPESA PARCELADA ===")

# Simular dados do formulário
form_data = {
    'descricao': 'Teste Debug Form',
    'valor_total': '600,00',  # Formato brasileiro
    'categoria': '9',  # Categoria válida
    'conta': '10',  # Conta válida 
    'responsavel': 'Teste',
    'total_parcelas': '6',
    'data_primeira_parcela': '2024-01-15',
    'intervalo': 'mensal'
}

print(f"Dados do formulário simulado: {form_data}")

# Testar conversão do valor
valor_str = form_data['valor_total']
print(f"\nValor original: '{valor_str}'")

try:
    valor_decimal = parse_currency_value(valor_str)
    print(f"Valor convertido: {valor_decimal}")
    print(f"Tipo: {type(valor_decimal)}")
except Exception as e:
    print(f"Erro na conversão: {e}")
    sys.exit(1)

# Verificar se categoria e conta existem
try:
    categoria = Categoria.objects.get(id=form_data['categoria'])
    print(f"\nCategoria encontrada: {categoria.nome} (ID: {categoria.id})")
except Categoria.DoesNotExist:
    print(f"\nERRO: Categoria ID {form_data['categoria']} não encontrada")
    sys.exit(1)

try:
    conta = Conta.objects.get(id=form_data['conta'])
    print(f"Conta encontrada: {conta.nome} (ID: {conta.id})")
except Conta.DoesNotExist:
    print(f"ERRO: Conta ID {form_data['conta']} não encontrada")
    sys.exit(1)

# Criar despesa parcelada
print(f"\n=== CRIANDO DESPESA PARCELADA ===")
try:
    despesa_parcelada = DespesaParcelada.objects.create(
        descricao=form_data['descricao'],
        valor_total=valor_decimal,
        categoria=categoria,
        conta=conta,
        responsavel=form_data['responsavel'],
        numero_parcelas=int(form_data['total_parcelas']),
        data_primeira_parcela=date(2024, 1, 15),
        intervalo_tipo=form_data['intervalo']
    )
    
    print(f"✅ Despesa criada com sucesso!")
    print(f"   ID: {despesa_parcelada.id}")
    print(f"   Descrição: {despesa_parcelada.descricao}")
    print(f"   Valor Total: {despesa_parcelada.valor_total}")
    print(f"   Número de Parcelas: {despesa_parcelada.numero_parcelas}")
    print(f"   Valor por Parcela: {despesa_parcelada.valor_parcela}")
    print(f"   Tenant ID: {despesa_parcelada.tenant_id}")
    
    # Gerar parcelas
    print(f"\n=== GERANDO PARCELAS ===")
    despesa_parcelada.gerar_parcelas()
    
    # Verificar parcelas geradas
    from financas.models import Transacao
    parcelas = Transacao.objects.filter(despesa_parcelada=despesa_parcelada)
    print(f"Parcelas geradas: {parcelas.count()}")
    
    for i, parcela in enumerate(parcelas, 1):
        print(f"  Parcela {i}: R$ {parcela.valor} - Vencimento: {parcela.data} - Tenant: {parcela.tenant_id}")
        
except Exception as e:
    print(f"❌ Erro ao criar despesa: {e}")
    import traceback
    traceback.print_exc()