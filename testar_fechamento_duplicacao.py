#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Conta, Transacao, FechamentoMensal, Categoria
from decimal import Decimal
from datetime import datetime, date

print("=== TESTE DE DUPLICAÇÃO NO FECHAMENTO ===")

# Limpar dados primeiro
Transacao.objects.all().delete()
FechamentoMensal.objects.all().delete()

# Verificar/criar categoria padrão
categoria, created = Categoria.objects.get_or_create(
    nome='Teste',
    defaults={'tipo': 'receita'}
)
if created:
    print(f"✅ Categoria criada: {categoria.nome}")
else:
    print(f"✅ Categoria encontrada: {categoria.nome}")

# Resetar saldo da conta
conta = Conta.objects.first()
if not conta:
    print("❌ Nenhuma conta encontrada!")
    exit()

conta.saldo = Decimal('0.00')
conta.save()

print(f"✅ Sistema limpo. Saldo inicial da conta {conta.nome}: R$ {conta.saldo}")

# Criar algumas transações para agosto
print("\n=== CRIANDO TRANSAÇÕES PARA AGOSTO 2025 ===")

# Receita de R$ 100
transacao1 = Transacao.objects.create(
    tipo='receita',
    valor=Decimal('100.00'),
    descricao='Salário agosto',
    data=date(2025, 8, 15),
    conta=conta,
    categoria=categoria
)
print(f"Criada: {transacao1.descricao} - R$ {transacao1.valor}")

# Despesa de R$ 90
transacao2 = Transacao.objects.create(
    tipo='despesa',
    valor=Decimal('90.00'),
    descricao='Despesas agosto',
    data=date(2025, 8, 20),
    conta=conta,
    categoria=categoria
)
print(f"Criada: {transacao2.descricao} - R$ {transacao2.valor}")

# Verificar saldo após transações
conta.refresh_from_db()
print(f"\nSaldo da conta após transações: R$ {conta.saldo}")
print(f"Saldo esperado: R$ 10,00 (100 - 90)")

# Simular fechamento mensal (lógica similar à view)
print("\n=== SIMULANDO FECHAMENTO DE AGOSTO 2025 ===")

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

# Verificar fechamento anterior (não deve existir)
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

# AQUI ESTÁ O PROBLEMA: usar conta.saldo como saldo inicial
saldo_inicial = fechamento_anterior.saldo_final if fechamento_anterior else conta.saldo
saldo_final = saldo_inicial + receitas - despesas

print(f"\nCálculo do fechamento:")
print(f"- Saldo inicial: R$ {saldo_inicial} (vem do saldo atual da conta)")
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

# PROBLEMA: Atualizar saldo da conta para saldo_final
# Isso causa duplicação porque o saldo já estava correto!
print(f"\nSaldo da conta ANTES de atualizar: R$ {conta.saldo}")
conta.saldo = saldo_final
conta.save()
print(f"Saldo da conta APÓS atualizar: R$ {conta.saldo}")

print(f"\n⚠️ PROBLEMA IDENTIFICADO:")
print(f"- O saldo da conta já estava correto (R$ 10,00)")
print(f"- Mas foi 'atualizado' para R$ {saldo_final}")
print(f"- Isso causa duplicação quando o saldo inicial é baseado no saldo atual da conta")

print(f"\n=== SOLUÇÃO PROPOSTA ===")
print(f"- O saldo inicial do fechamento deve ser R$ 0,00 quando não há fechamento anterior")
print(f"- OU não atualizar o saldo da conta após o fechamento se ele já está correto")