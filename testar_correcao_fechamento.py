#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Conta, Transacao, FechamentoMensal, Categoria
from decimal import Decimal
from datetime import datetime, date

print("=== TESTE DA CORREÇÃO DO FECHAMENTO ===")

# Limpar dados primeiro
Transacao.objects.all().delete()
FechamentoMensal.objects.all().delete()

# Verificar/criar categoria padrão
categoria, created = Categoria.objects.get_or_create(
    nome='Teste',
    defaults={'tipo': 'receita'}
)

# Resetar saldo da conta
conta = Conta.objects.first()
conta.saldo = Decimal('0.00')
conta.save()

print(f"✅ Sistema limpo. Saldo inicial da conta {conta.nome}: R$ {conta.saldo}")

# Criar transações para agosto
print("\n=== CRIANDO TRANSAÇÕES PARA AGOSTO 2025 ===")

transacao1 = Transacao.objects.create(
    tipo='receita',
    valor=Decimal('100.00'),
    descricao='Salário agosto',
    data=date(2025, 8, 15),
    conta=conta,
    categoria=categoria
)
print(f"Criada: {transacao1.descricao} - R$ {transacao1.valor}")

transacao2 = Transacao.objects.create(
    tipo='despesa',
    valor=Decimal('90.00'),
    descricao='Despesas agosto',
    data=date(2025, 8, 20),
    conta=conta,
    categoria=categoria
)
print(f"Criada: {transacao2.descricao} - R$ {transacao2.valor}")

conta.refresh_from_db()
print(f"\nSaldo da conta após transações: R$ {conta.saldo}")
print(f"Saldo esperado: R$ 10,00")

# Simular fechamento com a CORREÇÃO
print("\n=== SIMULANDO FECHAMENTO CORRIGIDO ===")

mes = 8
ano = 2025
data_inicio = date(ano, mes, 1)
data_fim = date(ano, mes, 31)

# Calcular totais do mês
transacoes_mes = Transacao.objects.filter(
    data__gte=data_inicio,
    data__lte=data_fim,
    conta=conta
)

receitas = sum(t.valor for t in transacoes_mes.filter(tipo='receita'))
despesas = sum(t.valor for t in transacoes_mes.filter(tipo='despesa'))

print(f"Receitas do mês: R$ {receitas}")
print(f"Despesas do mês: R$ {despesas}")

# Verificar fechamento anterior
fechamento_anterior = FechamentoMensal.objects.filter(
    conta=conta,
    ano__lt=ano
).order_by('-ano', '-mes').first()

if not fechamento_anterior:
    fechamento_anterior = FechamentoMensal.objects.filter(
        conta=conta,
        ano=ano, 
        mes__lt=mes
    ).order_by('-mes').first()

print(f"\nFechamento anterior encontrado: {fechamento_anterior is not None}")

# CORREÇÃO APLICADA: saldo inicial = 0 quando não há fechamento anterior
saldo_inicial = fechamento_anterior.saldo_final if fechamento_anterior else Decimal('0.00')
saldo_final = saldo_inicial + receitas - despesas

print(f"\nCálculo CORRIGIDO do fechamento:")
print(f"- Saldo inicial: R$ {saldo_inicial} (CORRIGIDO: 0 quando não há fechamento anterior)")
print(f"- Receitas: R$ {receitas}")
print(f"- Despesas: R$ {despesas}")
print(f"- Saldo final calculado: R$ {saldo_final}")

# Criar fechamento
fechamento = FechamentoMensal.objects.create(
    mes=mes,
    ano=ano,
    conta=conta,
    saldo_inicial=saldo_inicial,
    total_receitas=receitas,
    total_despesas=despesas,
    saldo_final=saldo_final,
    fechado=True,
    data_inicio_periodo=data_inicio,
    data_fim_periodo=data_fim,
    data_fechamento=datetime.now()
)

print(f"\n✅ Fechamento criado: {fechamento}")
print(f"Saldo final no fechamento: R$ {fechamento.saldo_final}")

# Verificar se o saldo final está correto
print(f"\nSaldo da conta atual: R$ {conta.saldo}")
print(f"Saldo final do fechamento: R$ {fechamento.saldo_final}")

if conta.saldo == fechamento.saldo_final:
    print("\n🎉 CORREÇÃO FUNCIONOU! Os saldos estão consistentes.")
else:
    print(f"\n⚠️ Ainda há inconsistência: conta tem R$ {conta.saldo}, fechamento tem R$ {fechamento.saldo_final}")

# Testar criação de transações em setembro
print("\n=== TESTANDO TRANSAÇÕES EM SETEMBRO (APÓS FECHAMENTO) ===")

transacao3 = Transacao.objects.create(
    tipo='receita',
    valor=Decimal('200.00'),
    descricao='Salário setembro',
    data=date(2025, 9, 15),
    conta=conta,
    categoria=categoria
)
print(f"Criada: {transacao3.descricao} - R$ {transacao3.valor}")

conta.refresh_from_db()
print(f"\nSaldo da conta após transação de setembro: R$ {conta.saldo}")
print(f"Saldo esperado: R$ 210,00 (10 do fechamento + 200 da nova receita)")

if conta.saldo == Decimal('210.00'):
    print("\n🎉 PERFEITO! O sistema está funcionando corretamente após a correção.")
else:
    print(f"\n⚠️ Ainda há problema no cálculo do saldo.")