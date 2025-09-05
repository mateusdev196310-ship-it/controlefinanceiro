import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Transacao, Conta
from django.utils import timezone
from django.db.models import Sum

# Data atual para cálculos mensais
hoje = timezone.now().date()
inicio_mes = hoje.replace(day=1)

print(f"Data atual: {hoje}")
print(f"Início do mês: {inicio_mes}")
print()

# Verificar transações do mês atual
transacoes_mes = Transacao.objects.filter(data__gte=inicio_mes, data__lte=hoje)
print(f"Transações do mês atual ({transacoes_mes.count()}):")
for t in transacoes_mes:
    print(f"  {t.data} - {t.tipo} - {t.descricao} - R$ {t.valor}")
print()

# Calcular totais
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

print(f"Receitas do mês: R$ {total_receitas}")
print(f"Despesas do mês: R$ {total_despesas}")
print(f"Movimentação do mês: R$ {total_receitas - total_despesas}")
print()

# Verificar saldos das contas
contas = Conta.objects.all()
print("Saldos das contas:")
saldo_total = 0
for conta in contas:
    print(f"  {conta.nome}: R$ {conta.saldo}")
    saldo_total += conta.saldo

print(f"Saldo total das contas: R$ {saldo_total}")
print()

# Calcular saldo anterior
movimentacao_mes = total_receitas - total_despesas
saldo_anterior = saldo_total - movimentacao_mes
print(f"Saldo anterior calculado: R$ {saldo_anterior}")