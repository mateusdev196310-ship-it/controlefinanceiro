#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.utils import parse_currency_value
from decimal import Decimal

print("=== TESTANDO FUNÇÃO parse_currency_value ===")

# Testes com diferentes formatos
testes = [
    "600",           # Número simples
    "600.00",        # Formato americano
    "600,00",        # Formato brasileiro
    "1.234,56",      # Formato brasileiro com milhares
    "1,234.56",      # Formato americano com milhares
    "R$ 600,00",     # Com símbolo de moeda
    "600.0",         # Um decimal
    "600.5",         # Um decimal com valor
    "",              # String vazia
    None,            # Valor nulo
    "abc",           # Texto inválido
    "600abc",        # Número com texto
]

for teste in testes:
    try:
        resultado = parse_currency_value(teste)
        print(f"Entrada: '{teste}' -> Resultado: {resultado} (tipo: {type(resultado)})")
    except Exception as e:
        print(f"Entrada: '{teste}' -> ERRO: {e}")

print("\n=== TESTE ESPECÍFICO COM VALOR 600 ===")
try:
    valor_600 = parse_currency_value("600")
    print(f"parse_currency_value('600') = {valor_600}")
    print(f"Tipo: {type(valor_600)}")
    print(f"É zero? {valor_600 == Decimal('0.00')}")
    print(f"É 600? {valor_600 == Decimal('600.00')}")
except Exception as e:
    print(f"Erro ao processar '600': {e}")