#!/usr/bin/env python
"""Script para testar criação de transação diretamente."""

import os
import sys
import django
from decimal import Decimal
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Conta, Categoria, Transacao
from financas.services import TransacaoService

def test_criar_transacao():
    """Testa a criação de uma transação."""
    print("=== Teste de Criação de Transação ===")
    
    # Verificar se existem contas e categorias
    contas = Conta.objects.all()
    categorias = Categoria.objects.all()
    
    print(f"Contas disponíveis: {contas.count()}")
    for conta in contas:
        print(f"  - ID: {conta.id}, Nome: {conta.nome}, Saldo: {conta.saldo}")
    
    print(f"Categorias disponíveis: {categorias.count()}")
    for categoria in categorias:
        print(f"  - ID: {categoria.id}, Nome: {categoria.nome}")
    
    if not contas.exists():
        print("Criando conta de teste...")
        conta = Conta.objects.create(nome="Conta Teste", saldo=Decimal('1000.00'))
    else:
        conta = contas.first()
    
    if not categorias.exists():
        print("Criando categoria de teste...")
        categoria = Categoria.objects.create(nome="Categoria Teste")
    else:
        categoria = categorias.first()
    
    print(f"\nUsando conta: {conta.nome} (ID: {conta.id})")
    print(f"Usando categoria: {categoria.nome} (ID: {categoria.id})")
    
    try:
        print("\nCriando transação via service...")
        transacao = TransacaoService.criar_transacao(
            conta_id=conta.id,
            descricao="Teste de Transação",
            valor=Decimal('100.00'),
            tipo="receita",
            data=date.today(),
            categoria=categoria.nome
        )
        
        print(f"✅ Transação criada com sucesso!")
        print(f"   ID: {transacao.id}")
        print(f"   Descrição: {transacao.descricao}")
        print(f"   Valor: {transacao.valor}")
        print(f"   Tipo: {transacao.tipo}")
        print(f"   Data: {transacao.data}")
        print(f"   Categoria: {transacao.categoria}")
        
        # Verificar se foi salva no banco
        transacao_db = Transacao.objects.get(id=transacao.id)
        print(f"✅ Transação confirmada no banco de dados: {transacao_db.descricao}")
        
    except Exception as e:
        print(f"❌ Erro ao criar transação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_criar_transacao()