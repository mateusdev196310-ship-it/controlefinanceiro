#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Conta, Transacao, FechamentoMensal
from django.db.models import Sum
from datetime import datetime, date

print("=== INVESTIGAÇÃO DA DISCREPÂNCIA DE SALDO ===")

# Buscar a conta
conta = Conta.objects.first()
if not conta:
    print("Nenhuma conta encontrada!")
    exit()

print(f"Conta: {conta.nome}")
print(f"Saldo atual no sistema: R$ {conta.saldo}")
print(f"Saldo real na conta bancária (informado): R$ 15,00")
print(f"Diferença: R$ {15 - float(conta.saldo)}")

# Verificar todas as transações
transacoes = Transacao.objects.filter(conta=conta).order_by('data')
print(f"\nTotal de transações: {transacoes.count()}")

if transacoes.count() > 0:
    print("\n=== TODAS AS TRANSAÇÕES ===")
    for t in transacoes:
        status_pago = " (PAGO)" if hasattr(t, 'pago') and t.pago else " (PENDENTE)" if hasattr(t, 'pago') else ""
        print(f"- {t.data} | {t.tipo} | R$ {t.valor} | {t.descricao}{status_pago}")

# Verificar fechamentos mensais
fechamentos = FechamentoMensal.objects.filter(conta=conta).order_by('-ano', '-mes')
print(f"\n=== FECHAMENTOS MENSAIS ({fechamentos.count()}) ===")

for f in fechamentos:
    print(f"- {f.mes:02d}/{f.ano} | Saldo Final: R$ {f.saldo_final} | Fechado: {f.fechado}")
    if f.data_fim_periodo:
        print(f"  Período: até {f.data_fim_periodo}")

# Análise detalhada do cálculo de saldo
print("\n=== ANÁLISE DO CÁLCULO DE SALDO ===")

# Buscar último fechamento
ultimo_fechamento = fechamentos.filter(fechado=True).first()

if ultimo_fechamento:
    print(f"\nÚltimo fechamento: {ultimo_fechamento.mes:02d}/{ultimo_fechamento.ano}")
    print(f"Saldo final do fechamento: R$ {ultimo_fechamento.saldo_final}")
    
    # Transações após o fechamento
    data_limite = ultimo_fechamento.data_fim_periodo or ultimo_fechamento.criado_em.date()
    print(f"Data limite do fechamento: {data_limite}")
    
    transacoes_pos_fechamento = transacoes.filter(data__gt=data_limite)
    print(f"\nTransações após fechamento: {transacoes_pos_fechamento.count()}")
    
    if transacoes_pos_fechamento.count() > 0:
        print("\nTransações pós-fechamento:")
        for t in transacoes_pos_fechamento:
            status_pago = " (PAGO)" if hasattr(t, 'pago') and t.pago else " (PENDENTE)" if hasattr(t, 'pago') else ""
            print(f"- {t.data} | {t.tipo} | R$ {t.valor} | {t.descricao}{status_pago}")
        
        # Calcular receitas e despesas pós-fechamento
        receitas_pos = transacoes_pos_fechamento.filter(tipo='entrada').aggregate(total=Sum('valor'))['total'] or 0
        despesas_pos = transacoes_pos_fechamento.filter(tipo='saida').aggregate(total=Sum('valor'))['total'] or 0
        
        # Verificar se há transações não pagas
        transacoes_nao_pagas = transacoes_pos_fechamento.filter(pago=False) if hasattr(Transacao, 'pago') else []
        
        print(f"\nReceitas pós-fechamento: R$ {receitas_pos}")
        print(f"Despesas pós-fechamento: R$ {despesas_pos}")
        
        if transacoes_nao_pagas:
            print(f"\nTransações NÃO PAGAS: {len(transacoes_nao_pagas)}")
            for t in transacoes_nao_pagas:
                print(f"- {t.data} | {t.tipo} | R$ {t.valor} | {t.descricao} (NÃO PAGO)")
        
        saldo_esperado = ultimo_fechamento.saldo_final + receitas_pos - despesas_pos
        print(f"\nSaldo esperado: R$ {ultimo_fechamento.saldo_final} + R$ {receitas_pos} - R$ {despesas_pos} = R$ {saldo_esperado}")
        print(f"Saldo no sistema: R$ {conta.saldo}")
        print(f"Diferença sistema vs esperado: R$ {float(conta.saldo) - float(saldo_esperado)}")
else:
    print("\nNenhum fechamento encontrado")
    # Calcular saldo total
    receitas_total = transacoes.filter(tipo='entrada').aggregate(total=Sum('valor'))['total'] or 0
    despesas_total = transacoes.filter(tipo='saida').aggregate(total=Sum('valor'))['total'] or 0
    saldo_calculado = receitas_total - despesas_total
    
    print(f"Receitas totais: R$ {receitas_total}")
    print(f"Despesas totais: R$ {despesas_total}")
    print(f"Saldo calculado: R$ {saldo_calculado}")
    print(f"Saldo no sistema: R$ {conta.saldo}")
    print(f"Diferença: R$ {float(conta.saldo) - float(saldo_calculado)}")

# Verificar se há problema com transações não pagas
if hasattr(Transacao, 'pago'):
    transacoes_nao_pagas_total = transacoes.filter(pago=False, tipo='saida')
    if transacoes_nao_pagas_total.exists():
        valor_nao_pago = transacoes_nao_pagas_total.aggregate(total=Sum('valor'))['total'] or 0
        print(f"\n=== POSSÍVEL PROBLEMA ===")
        print(f"Despesas não pagas: R$ {valor_nao_pago}")
        print("Essas despesas podem não estar sendo descontadas do saldo!")

print("\n=== RECOMENDAÇÕES ===")
print("1. Verificar se todas as transações estão marcadas como pagas quando apropriado")
print("2. Verificar se o método atualizar_saldo() está considerando apenas transações pagas")
print("3. Comparar com extrato bancário real")