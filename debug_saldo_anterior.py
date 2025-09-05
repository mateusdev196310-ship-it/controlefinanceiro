import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Transacao, Conta
from django.utils import timezone
from django.db.models import Sum

# Data atual
hoje = timezone.now().date()
inicio_mes = hoje.replace(day=1)

print("=== TESTE DA NOVA LÓGICA ===")
print(f"Data hoje: {hoje}")
print(f"Início do mês: {inicio_mes}")
print()

# Transações do mês atual
receitas_mes = Transacao.objects.filter(
    tipo='receita', 
    data__gte=inicio_mes,
    data__lte=hoje
).aggregate(total=Sum('valor'))

despesas_mes = Transacao.objects.filter(
    tipo='despesa', 
    data__gte=inicio_mes,
    data__lte=hoje
).aggregate(total=Sum('valor'))

total_receitas = receitas_mes['total'] if receitas_mes['total'] else 0
total_despesas = despesas_mes['total'] if despesas_mes['total'] else 0

print(f"Receitas do mês atual: R$ {total_receitas}")
print(f"Despesas do mês atual: R$ {total_despesas}")
print(f"Movimentação do mês: R$ {total_receitas - total_despesas}")
print()

# Nova lógica para saldo anterior
transacoes_anteriores = Transacao.objects.filter(data__lt=inicio_mes)
receitas_anteriores = transacoes_anteriores.filter(tipo='receita').aggregate(total=Sum('valor'))['total'] or 0
despesas_anteriores = transacoes_anteriores.filter(tipo='despesa').aggregate(total=Sum('valor'))['total'] or 0
saldo_anterior_novo = receitas_anteriores - despesas_anteriores

print(f"Receitas anteriores ao mês: R$ {receitas_anteriores}")
print(f"Despesas anteriores ao mês: R$ {despesas_anteriores}")
print(f"Saldo anterior (nova lógica): R$ {saldo_anterior_novo}")
print()

# Saldo atual
contas_saldo = Conta.objects.aggregate(total=Sum('saldo'))
saldo_atual = contas_saldo['total'] if contas_saldo['total'] else 0
print(f"Saldo atual: R$ {saldo_atual}")
print()

# Verificação: saldo anterior + movimentação do mês = saldo atual?
verificacao = saldo_anterior_novo + (total_receitas - total_despesas)
print(f"Verificação: {saldo_anterior_novo} + {total_receitas - total_despesas} = {verificacao}")
print(f"Saldo atual das contas: {saldo_atual}")
print(f"Verificação está correta: {verificacao == saldo_atual}")