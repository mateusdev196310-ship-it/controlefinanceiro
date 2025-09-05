#!/usr/bin/env python
import os
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import DespesaParcelada, Categoria, Conta
from financas.utils import parse_currency_value
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definir tenant_id
connection.tenant_id = 5

print("=== Teste de Simulação do Formulário Web ===")
print(f"Tenant ID: {connection.tenant_id}")

# Simular dados que podem vir do formulário web
# Testando diferentes formatos que o JavaScript pode enviar
test_cases = [
    {
        'name': 'Formato simples (600)',
        'valor_total': '600',
        'descricao': 'Teste Formato Simples'
    },
    {
        'name': 'Formato com vírgula (600,00)',
        'valor_total': '600,00',
        'descricao': 'Teste Formato Vírgula'
    },
    {
        'name': 'Formato com R$ (R$ 600,00)',
        'valor_total': 'R$ 600,00',
        'descricao': 'Teste Formato R$'
    },
    {
        'name': 'Formato vazio',
        'valor_total': '',
        'descricao': 'Teste Formato Vazio'
    },
    {
        'name': 'Formato com espaços',
        'valor_total': ' 600,00 ',
        'descricao': 'Teste Formato Espaços'
    }
]

# Obter categoria e conta válidas
categoria = Categoria.objects.filter(tenant_id=5).first()
conta = Conta.objects.filter(tenant_id=5).first()

if not categoria or not conta:
    print("Erro: Categoria ou conta não encontrada para tenant_id=5")
    exit(1)

print(f"Usando categoria: {categoria.nome} (ID: {categoria.id})")
print(f"Usando conta: {conta.nome} (ID: {conta.id})")
print()

for test_case in test_cases:
    print(f"--- {test_case['name']} ---")
    print(f"Valor original: '{test_case['valor_total']}'")
    
    # Converter usando parse_currency_value
    valor_convertido = parse_currency_value(test_case['valor_total'])
    print(f"Valor convertido: {valor_convertido}")
    
    if valor_convertido > 0:
        try:
            # Simular criação da despesa parcelada
            despesa = DespesaParcelada.objects.create(
                descricao=test_case['descricao'],
                valor_total=valor_convertido,
                categoria=categoria,
                conta=conta,
                responsavel='Teste',
                numero_parcelas=3,
                data_primeira_parcela=datetime(2024, 6, 15).date(),
                intervalo_tipo='mensal'
            )
            
            print(f"Despesa criada: ID={despesa.id}, valor_total={despesa.valor_total}")
            print(f"Valor da parcela: {despesa.valor_parcela}")
            
            # Gerar parcelas
            despesa.gerar_parcelas()
            print(f"Parcelas geradas: {despesa.get_parcelas().count()}")
            
        except Exception as e:
            print(f"Erro ao criar despesa: {e}")
    else:
        print("Valor zero - não criando despesa")
    
    print()

print("=== Teste concluído ===")