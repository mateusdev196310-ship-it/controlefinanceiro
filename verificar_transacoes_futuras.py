#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Transacao
from django.utils import timezone

# Data atual
hoje = timezone.now().date()
print(f"Data atual: {hoje}")

# Buscar todas as transações futuras
futuras = Transacao.objects.filter(data__gt=hoje).order_by('data')
print(f"\nTotal de transações futuras: {futuras.count()}")

if futuras.exists():
    print("\nTransações futuras encontradas:")
    print("-" * 80)
    
    for t in futuras:
        print(f"ID: {t.id:4d} | Data: {t.data} | Tipo: {t.tipo:8s} | "
              f"Valor: R$ {t.valor:8.2f} | Conta: {t.conta.nome} | "
              f"Descrição: {t.descricao[:30]}...")
    
    # Estatísticas por tipo
    print("\n" + "="*80)
    print("ESTATÍSTICAS POR TIPO:")
    
    receitas_futuras = futuras.filter(tipo='receita')
    despesas_futuras = futuras.filter(tipo='despesa')
    
    print(f"Receitas futuras: {receitas_futuras.count()}")
    if receitas_futuras.exists():
        total_receitas = sum(t.valor for t in receitas_futuras)
        print(f"  Total em receitas futuras: R$ {total_receitas:.2f}")
    
    print(f"Despesas futuras: {despesas_futuras.count()}")
    if despesas_futuras.exists():
        total_despesas = sum(t.valor for t in despesas_futuras)
        print(f"  Total em despesas futuras: R$ {total_despesas:.2f}")
    
    # Verificar se há transações relacionadas a contas a receber
    print("\n" + "="*80)
    print("ANÁLISE DE POSSÍVEIS PROBLEMAS:")
    
    suspeitas = futuras.filter(
        descricao__icontains='receber'
    ) | futuras.filter(
        descricao__icontains='saldo inicial'
    ) | futuras.filter(
        responsavel='Sistema'
    )
    
    if suspeitas.exists():
        print(f"\nTransações suspeitas (possível erro de rotina): {suspeitas.count()}")
        for t in suspeitas:
            print(f"  ID: {t.id} | {t.data} | {t.tipo} | R$ {t.valor} | {t.descricao}")
    else:
        print("\nNenhuma transação suspeita identificada.")
        
else:
    print("\nNenhuma transação futura encontrada.")

print("\n" + "="*80)
print("VERIFICAÇÃO CONCLUÍDA")