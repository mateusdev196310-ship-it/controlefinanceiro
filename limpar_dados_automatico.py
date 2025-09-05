#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Conta, Transacao, FechamentoMensal, DespesaParcelada
from decimal import Decimal

print("=== LIMPEZA COMPLETA DOS DADOS (AUTOMÁTICA) ===")
print("Limpando:")
print("- Todas as transações")
print("- Todos os fechamentos mensais")
print("- Todas as despesas parceladas")
print("- Resetar saldo das contas para R$ 0,00")
print()

print("Iniciando limpeza...")

try:
    # 1. Deletar todas as transações
    transacoes_count = Transacao.objects.count()
    Transacao.objects.all().delete()
    print(f"✅ {transacoes_count} transações deletadas")
    
    # 2. Deletar todos os fechamentos mensais
    fechamentos_count = FechamentoMensal.objects.count()
    FechamentoMensal.objects.all().delete()
    print(f"✅ {fechamentos_count} fechamentos mensais deletados")
    
    # 3. Deletar todas as despesas parceladas
    despesas_parceladas_count = DespesaParcelada.objects.count()
    DespesaParcelada.objects.all().delete()
    print(f"✅ {despesas_parceladas_count} despesas parceladas deletadas")
    
    # 4. Resetar saldo de todas as contas para R$ 0,00
    contas = Conta.objects.all()
    contas_count = contas.count()
    
    for conta in contas:
        conta.saldo = Decimal('0.00')
        conta.save()
    
    print(f"✅ Saldo de {contas_count} conta(s) resetado para R$ 0,00")
    
    print("\n=== LIMPEZA CONCLUÍDA COM SUCESSO! ===")
    print("\nEstado atual:")
    print(f"- Transações: {Transacao.objects.count()}")
    print(f"- Fechamentos: {FechamentoMensal.objects.count()}")
    print(f"- Despesas parceladas: {DespesaParcelada.objects.count()}")
    
    print("\nContas:")
    for conta in Conta.objects.all():
        print(f"- {conta.nome}: R$ {conta.saldo}")
    
    print("\n🎉 Sistema limpo e pronto para novos testes!")
    
except Exception as e:
    print(f"❌ Erro durante a limpeza: {str(e)}")
    print("Verifique o console para mais detalhes.")