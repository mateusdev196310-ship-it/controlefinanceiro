#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from financas.models import ContaReceber, Transacao
from django.db import transaction

def refatorar_contas_receber():
    """Remove completamente o sistema atual de contas a receber"""
    
    print("=== REFATORAÇÃO DO SISTEMA DE CONTAS A RECEBER ===")
    print("\n1. Removendo todas as transações relacionadas a contas a receber...")
    
    with transaction.atomic():
        # Remover todas as transações de contas a receber
        transacoes_removidas = Transacao.objects.filter(conta_receber__isnull=False).count()
        Transacao.objects.filter(conta_receber__isnull=False).delete()
        print(f"   ✓ {transacoes_removidas} transações removidas")
        
        # Remover todas as contas a receber
        contas_removidas = ContaReceber.objects.count()
        ContaReceber.objects.all().delete()
        print(f"   ✓ {contas_removidas} contas a receber removidas")
        
        print("\n2. Verificando limpeza...")
        transacoes_restantes = Transacao.objects.filter(conta_receber__isnull=False).count()
        contas_restantes = ContaReceber.objects.count()
        
        print(f"   - Transações restantes: {transacoes_restantes}")
        print(f"   - Contas a receber restantes: {contas_restantes}")
        
        if transacoes_restantes == 0 and contas_restantes == 0:
            print("\n✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
            print("\nPróximos passos:")
            print("1. Atualizar o modelo ContaReceber no models.py")
            print("2. Criar e executar migrations")
            print("3. Recriar as views baseadas em DespesaParcelada")
            print("4. Adaptar os templates")
        else:
            print("\n❌ ERRO: Ainda existem dados não removidos")
            return False
    
    return True

if __name__ == '__main__':
    try:
        sucesso = refatorar_contas_receber()
        if sucesso:
            print("\n🎉 Refatoração iniciada com sucesso!")
        else:
            print("\n💥 Erro durante a refatoração")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erro inesperado: {str(e)}")
        sys.exit(1)