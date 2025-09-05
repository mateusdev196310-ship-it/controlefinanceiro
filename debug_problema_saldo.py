#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Conta, Transacao, FechamentoMensal
from django.db.models import Sum
from decimal import Decimal

print("=== INVESTIGAÇÃO DO PROBLEMA DE SALDO ===")

# Verificar estado atual
conta = Conta.objects.first()
if not conta:
    print("Nenhuma conta encontrada!")
    exit()

print(f"Conta: {conta.nome}")
print(f"Saldo atual na conta: R$ {conta.saldo}")
print(f"Saldo esperado: R$ 0,00 (após limpeza)")

# Verificar transações
transacoes = Transacao.objects.filter(conta=conta)
print(f"\nTransações encontradas: {transacoes.count()}")

if transacoes.exists():
    print("\n=== TRANSAÇÕES EXISTENTES ===")
    for t in transacoes:
        print(f"- {t.data} | {t.tipo} | R$ {t.valor} | {t.descricao}")
else:
    print("✅ Nenhuma transação encontrada (correto após limpeza)")

# Verificar fechamentos
fechamentos = FechamentoMensal.objects.filter(conta=conta)
print(f"\nFechamentos encontrados: {fechamentos.count()}")

if fechamentos.exists():
    print("\n=== FECHAMENTOS EXISTENTES ===")
    for f in fechamentos:
        print(f"- {f.mes:02d}/{f.ano} | Saldo Final: R$ {f.saldo_final} | Fechado: {f.fechado}")
        if f.data_fim_periodo:
            print(f"  Período: até {f.data_fim_periodo}")
else:
    print("✅ Nenhum fechamento encontrado (correto após limpeza)")

# Verificar se há problema no método atualizar_saldo
print("\n=== TESTE DO MÉTODO ATUALIZAR_SALDO ===")
print(f"Saldo antes da atualização: R$ {conta.saldo}")

try:
    novo_saldo = conta.atualizar_saldo()
    print(f"Saldo após atualização: R$ {novo_saldo}")
    
    # Recarregar da base de dados
    conta.refresh_from_db()
    print(f"Saldo na base de dados: R$ {conta.saldo}")
    
except Exception as e:
    print(f"❌ Erro ao atualizar saldo: {str(e)}")

# Forçar saldo para zero se necessário
if conta.saldo != Decimal('0.00'):
    print("\n=== CORREÇÃO FORÇADA ===")
    print(f"Forçando saldo de R$ {conta.saldo} para R$ 0,00...")
    
    # Usar update direto para evitar signals
    Conta.objects.filter(id=conta.id).update(saldo=Decimal('0.00'))
    conta.refresh_from_db()
    
    print(f"✅ Saldo corrigido: R$ {conta.saldo}")
else:
    print("\n✅ Saldo já está correto: R$ 0,00")

print("\n=== VERIFICAÇÃO FINAL ===")
print(f"- Transações: {Transacao.objects.count()}")
print(f"- Fechamentos: {FechamentoMensal.objects.count()}")
print(f"- Saldo da conta {conta.nome}: R$ {conta.saldo}")

if conta.saldo == Decimal('0.00') and not transacoes.exists() and not fechamentos.exists():
    print("\n🎉 Sistema completamente limpo e correto!")
else:
    print("\n⚠️ Ainda há inconsistências no sistema.")