#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Conta, Transacao, FechamentoMensal
from django.db.models import Sum
from datetime import datetime, date

print("=== VERIFICAÇÃO DO SALDO CORRIGIDO (SEM LÓGICA DE PAGO) ===")

# Buscar a conta
conta = Conta.objects.first()
if not conta:
    print("Nenhuma conta encontrada!")
    exit()

print(f"Conta: {conta.nome}")
print(f"Saldo atual no sistema: R$ {conta.saldo}")

# Verificar todas as transações
transacoes = Transacao.objects.filter(conta=conta).order_by('data')
print(f"\nTotal de transações: {transacoes.count()}")

if transacoes.count() > 0:
    print("\n=== TODAS AS TRANSAÇÕES ===")
    for t in transacoes:
        print(f"- {t.data} | {t.tipo} | R$ {t.valor} | {t.descricao}")

# Verificar fechamentos mensais
fechamentos = FechamentoMensal.objects.filter(conta=conta).order_by('-ano', '-mes')
print(f"\n=== FECHAMENTOS MENSAIS ({fechamentos.count()}) ===")

for f in fechamentos:
    print(f"- {f.mes:02d}/{f.ano} | Saldo Final: R$ {f.saldo_final} | Fechado: {f.fechado}")
    if f.data_fim_periodo:
        print(f"  Período: até {f.data_fim_periodo}")

# Cálculo manual do saldo correto
print("\n=== CÁLCULO MANUAL DO SALDO CORRETO ===")

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
            print(f"- {t.data} | {t.tipo} | R$ {t.valor} | {t.descricao}")
        
        # Calcular receitas e despesas pós-fechamento (TODAS as transações)
        receitas_pos = transacoes_pos_fechamento.filter(tipo='receita').aggregate(total=Sum('valor'))['total'] or 0
        despesas_pos = transacoes_pos_fechamento.filter(tipo='despesa').aggregate(total=Sum('valor'))['total'] or 0
        
        print(f"\nReceitas pós-fechamento: R$ {receitas_pos}")
        print(f"Despesas pós-fechamento: R$ {despesas_pos}")
        
        saldo_esperado = ultimo_fechamento.saldo_final + receitas_pos - despesas_pos
        print(f"\nSaldo esperado: R$ {ultimo_fechamento.saldo_final} + R$ {receitas_pos} - R$ {despesas_pos} = R$ {saldo_esperado}")
        print(f"Saldo no sistema: R$ {conta.saldo}")
        
        if float(conta.saldo) == float(saldo_esperado):
            print("✅ SALDO CORRETO!")
        else:
            print(f"❌ DIFERENÇA: R$ {float(conta.saldo) - float(saldo_esperado)}")
            print("\nForçando atualização do saldo...")
            conta.atualizar_saldo()
            conta.refresh_from_db()
            print(f"Novo saldo após atualização: R$ {conta.saldo}")
else:
    print("\nNenhum fechamento encontrado")
    # Calcular saldo total
    receitas_total = transacoes.filter(tipo='receita').aggregate(total=Sum('valor'))['total'] or 0
    despesas_total = transacoes.filter(tipo='despesa').aggregate(total=Sum('valor'))['total'] or 0
    saldo_calculado = receitas_total - despesas_total
    
    print(f"Receitas totais: R$ {receitas_total}")
    print(f"Despesas totais: R$ {despesas_total}")
    print(f"Saldo calculado: R$ {saldo_calculado}")
    print(f"Saldo no sistema: R$ {conta.saldo}")
    
    if float(conta.saldo) == float(saldo_calculado):
        print("✅ SALDO CORRETO!")
    else:
        print(f"❌ DIFERENÇA: R$ {float(conta.saldo) - float(saldo_calculado)}")

print("\n=== CONCLUSÃO ===")
print("Agora o sistema considera TODAS as transações, independente do status 'pago'.")
print("O campo 'pago' será usado apenas para despesas parceladas no futuro.")