#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Conta, Transacao, FechamentoMensal
from django.db.models import Sum

print("=== INVESTIGAÇÃO DO SALDO ===")

# Buscar a conta
conta = Conta.objects.first()
if not conta:
    print("Nenhuma conta encontrada!")
    exit()

print(f"Conta: {conta.nome}")
print(f"Saldo atual no banco: R$ {conta.saldo}")
print(f"Tipo: {conta.tipo}")

# Verificar transações
transacoes = Transacao.objects.filter(conta=conta)
print(f"\nTotal de transações: {transacoes.count()}")

if transacoes.count() > 0:
    print("\nTransações encontradas:")
    for t in transacoes:
        print(f"- {t.data} | {t.tipo} | R$ {t.valor} | {t.descricao}")
else:
    print("Nenhuma transação encontrada")

# Verificar fechamentos mensais
fechamentos = FechamentoMensal.objects.filter(conta=conta)
print(f"\nTotal de fechamentos: {fechamentos.count()}")

if fechamentos.count() > 0:
    print("\nFechamentos encontrados:")
    for f in fechamentos.order_by('-ano', '-mes'):
        print(f"- {f.mes}/{f.ano} | Saldo Final: R$ {f.saldo_final} | Fechado: {f.fechado}")

# Calcular saldo baseado nas transações
receitas = transacoes.filter(tipo='entrada').aggregate(total=Sum('valor'))['total'] or 0
despesas = transacoes.filter(tipo='saida').aggregate(total=Sum('valor'))['total'] or 0
saldo_calculado = receitas - despesas

print(f"\n=== CÁLCULO MANUAL ===")
print(f"Receitas: R$ {receitas}")
print(f"Despesas: R$ {despesas}")
print(f"Saldo calculado: R$ {saldo_calculado}")
print(f"Saldo no banco: R$ {conta.saldo}")
print(f"Diferença: R$ {conta.saldo - saldo_calculado}")

# Verificar se há saldo inicial em fechamentos
ultimo_fechamento = fechamentos.filter(fechado=True).order_by('-ano', '-mes').first()
if ultimo_fechamento:
    print(f"\nÚltimo fechamento: {ultimo_fechamento.mes}/{ultimo_fechamento.ano}")
    print(f"Saldo final do fechamento: R$ {ultimo_fechamento.saldo_final}")
    
    # Transações após o fechamento
    data_limite = ultimo_fechamento.data_fim_periodo or ultimo_fechamento.criado_em.date()
    transacoes_pos_fechamento = transacoes.filter(data__gt=data_limite)
    print(f"Transações após fechamento: {transacoes_pos_fechamento.count()}")
    
    if transacoes_pos_fechamento.count() > 0:
        receitas_pos = transacoes_pos_fechamento.filter(tipo='entrada').aggregate(total=Sum('valor'))['total'] or 0
        despesas_pos = transacoes_pos_fechamento.filter(tipo='saida').aggregate(total=Sum('valor'))['total'] or 0
        saldo_esperado = ultimo_fechamento.saldo_final + receitas_pos - despesas_pos
        
        print(f"Receitas pós-fechamento: R$ {receitas_pos}")
        print(f"Despesas pós-fechamento: R$ {despesas_pos}")
        print(f"Saldo esperado: R$ {saldo_esperado}")
else:
    print("\nNenhum fechamento encontrado")