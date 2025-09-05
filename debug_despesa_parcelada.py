#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import DespesaParcelada, Transacao, Categoria, Conta, CustomUser
from django.db import connection

def debug_despesa_parcelada():
    print("=== DEBUG DESPESA PARCELADA ===")
    print(f"Connection tenant_id: {getattr(connection, 'tenant_id', 'N/A')}")
    print(f"Connection schema_name: {getattr(connection, 'schema_name', 'N/A')}")
    print()
    
    # Verificar usuários
    print("=== USUÁRIOS ===")
    users = CustomUser.objects.all()
    for user in users:
        print(f"User ID: {user.id}, Username: {user.username}, Email: {user.email}, Tenant ID: {getattr(user, 'tenant_id', 'N/A')}")
    print()
    
    # Verificar despesas parceladas
    print("=== DESPESAS PARCELADAS ===")
    despesas = DespesaParcelada.objects.all()
    print(f"Total de despesas parceladas: {despesas.count()}")
    
    for despesa in despesas:
        print(f"\nDespesa ID: {despesa.id}")
        print(f"Descrição: {despesa.descricao}")
        print(f"Valor Total: {despesa.valor_total}")
        print(f"Número de Parcelas: {despesa.numero_parcelas}")
        print(f"Tenant ID: {getattr(despesa, 'tenant_id', 'N/A')}")
        print(f"Criada em: {despesa.criada_em}")
        
        # Verificar parcelas (transações)
        parcelas = despesa.get_parcelas()
        print(f"Parcelas encontradas: {len(parcelas)}")
        
        for i, parcela in enumerate(parcelas[:3], 1):  # Mostrar apenas as 3 primeiras
            print(f"  Parcela {i}: ID={parcela.id}, Valor={parcela.valor}, Data={parcela.data}, Tenant ID={getattr(parcela, 'tenant_id', 'N/A')}")
        
        if len(parcelas) > 3:
            print(f"  ... e mais {len(parcelas) - 3} parcelas")
    
    print()
    
    # Verificar transações relacionadas a despesas parceladas
    print("=== TRANSAÇÕES DE DESPESAS PARCELADAS ===")
    transacoes_parceladas = Transacao.objects.filter(despesa_parcelada__isnull=False)
    print(f"Total de transações de despesas parceladas: {transacoes_parceladas.count()}")
    
    for transacao in transacoes_parceladas[:5]:  # Mostrar apenas as 5 primeiras
        print(f"Transação ID: {transacao.id}, Despesa ID: {transacao.despesa_parcelada.id}, Valor: {transacao.valor}, Tenant ID: {getattr(transacao, 'tenant_id', 'N/A')}")
    
    print()
    
    # Verificar categorias e contas
    print("=== CATEGORIAS ===")
    categorias = Categoria.objects.all()
    print(f"Total de categorias: {categorias.count()}")
    for cat in categorias[:3]:
        print(f"Categoria ID: {cat.id}, Nome: {cat.nome}, Tenant ID: {getattr(cat, 'tenant_id', 'N/A')}")
    
    print()
    
    print("=== CONTAS ===")
    contas = Conta.objects.all()
    print(f"Total de contas: {contas.count()}")
    for conta in contas[:3]:
        print(f"Conta ID: {conta.id}, Nome: {conta.nome}, Tenant ID: {getattr(conta, 'tenant_id', 'N/A')}")
    
    print()
    
    # Tentar buscar despesa específica ID 7
    print("=== BUSCA ESPECÍFICA DESPESA ID 7 ===")
    try:
        despesa_7 = DespesaParcelada.objects.get(id=7)
        print(f"Despesa ID 7 encontrada: {despesa_7.descricao}")
        print(f"Tenant ID: {getattr(despesa_7, 'tenant_id', 'N/A')}")
    except DespesaParcelada.DoesNotExist:
        print("Despesa ID 7 NÃO encontrada")
        
        # Verificar se existe em outros schemas
        print("\nVerificando em todos os schemas...")
        from django.db import connections
        from django.conf import settings
        
        # Tentar buscar diretamente no banco
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, descricao, tenant_id FROM financas_despesaparcelada WHERE id = 7")
            result = cursor.fetchone()
            if result:
                print(f"Encontrada no banco: ID={result[0]}, Descrição={result[1]}, Tenant ID={result[2]}")
            else:
                print("Não encontrada nem no banco de dados")
    
    print("\n=== FIM DEBUG ===")

if __name__ == '__main__':
    debug_despesa_parcelada()