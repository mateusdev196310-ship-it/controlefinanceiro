#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import ContaReceber, Transacao
from django.db import transaction

def excluir_todas_contas_receber():
    """Remove completamente todas as contas a receber e dados relacionados"""
    
    print("Iniciando exclusão completa das contas a receber...")
    
    with transaction.atomic():
        # 1. Buscar todas as transações relacionadas a contas a receber
        transacoes_contas_receber = Transacao.objects.filter(
            conta_receber__isnull=False
        )
        
        total_transacoes = transacoes_contas_receber.count()
        print(f"Encontradas {total_transacoes} transações relacionadas a contas a receber")
        
        if total_transacoes > 0:
            # Excluir todas as transações relacionadas
            transacoes_contas_receber.delete()
            print(f"✓ {total_transacoes} transações excluídas")
        
        # 2. Buscar todas as contas a receber
        contas_receber = ContaReceber.objects.all()
        total_contas = contas_receber.count()
        print(f"Encontradas {total_contas} contas a receber")
        
        if total_contas > 0:
            # Listar as contas que serão excluídas
            for conta in contas_receber:
                print(f"  - {conta.descricao} (ID: {conta.id})")
            
            # Excluir todas as contas a receber
            contas_receber.delete()
            print(f"✓ {total_contas} contas a receber excluídas completamente")
        
        # 3. Verificar se ainda existem referências
        transacoes_restantes = Transacao.objects.filter(conta_receber__isnull=False).count()
        contas_restantes = ContaReceber.objects.all().count()
        
        print(f"\n📊 Verificação final:")
        print(f"  - Transações com conta_receber: {transacoes_restantes}")
        print(f"  - Contas a receber restantes: {contas_restantes}")
        
        if transacoes_restantes == 0 and contas_restantes == 0:
            print("\n✅ Exclusão completa realizada com sucesso!")
            print("Todos os dados relacionados a contas a receber foram removidos.")
        else:
            print("\n⚠️ Ainda existem dados relacionados no sistema.")

if __name__ == '__main__':
    try:
        excluir_todas_contas_receber()
    except Exception as e:
        print(f"❌ Erro durante a exclusão: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)