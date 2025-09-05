import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Conta

print("=== CORRIGINDO SALDOS DAS CONTAS ===")
print()

for conta in Conta.objects.all():
    saldo_antigo = conta.saldo
    saldo_novo = conta.atualizar_saldo()
    
    print(f"Conta: {conta.nome}")
    print(f"  Saldo antigo: R$ {saldo_antigo}")
    print(f"  Saldo novo: R$ {saldo_novo}")
    print(f"  Diferença: R$ {saldo_novo - saldo_antigo}")
    print()

print("Saldos corrigidos com sucesso!")