#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import DespesaParcelada, Transacao, Banco
from django.contrib.auth import get_user_model

def limpar_dados_teste():
    print("=== VERIFICANDO DADOS DE TESTE ===")
    
    # Buscar despesas parceladas teste
    despesas_teste = DespesaParcelada.objects.filter(descricao__icontains='teste')
    print(f"Despesas parceladas teste encontradas: {despesas_teste.count()}")
    for d in despesas_teste:
        print(f"  - {d.descricao} (ID: {d.id})")
    
    # Buscar transações teste
    transacoes_teste = Transacao.objects.filter(descricao__icontains='teste')
    print(f"Transações teste encontradas: {transacoes_teste.count()}")
    for t in transacoes_teste:
        print(f"  - {t.descricao} (ID: {t.id})")
    
    # Buscar bancos teste
    bancos_teste = Banco.objects.filter(nome__icontains='teste')
    print(f"Bancos teste encontrados: {bancos_teste.count()}")
    for b in bancos_teste:
        print(f"  - {b.nome} (ID: {b.id})")
    
    print("\n=== EXCLUINDO DADOS DE TESTE ===")
    
    # Primeiro: Excluir transações relacionadas às despesas parceladas teste
    transacoes_despesas_teste = Transacao.objects.filter(despesa_parcelada__in=despesas_teste)
    transacoes_despesas_deletadas = transacoes_despesas_teste.count()
    if transacoes_despesas_deletadas > 0:
        transacoes_despesas_teste.delete()
        print(f"✓ Transações de despesas parceladas excluídas: {transacoes_despesas_deletadas}")
    
    # Segundo: Excluir outras transações teste
    transacoes_deletadas = transacoes_teste.count()
    if transacoes_deletadas > 0:
        transacoes_teste.delete()
        print(f"✓ Transações teste excluídas: {transacoes_deletadas}")
    else:
        print("✓ Nenhuma transação teste encontrada")
    
    # Terceiro: Excluir despesas parceladas
    despesas_deletadas = despesas_teste.count()
    if despesas_deletadas > 0:
        despesas_teste.delete()
        print(f"✓ Despesas parceladas excluídas: {despesas_deletadas}")
    else:
        print("✓ Nenhuma despesa parcelada teste encontrada")
    
    # Quarto: Excluir bancos
    bancos_deletados = bancos_teste.count()
    if bancos_deletados > 0:
        bancos_teste.delete()
        print(f"✓ Bancos excluídos: {bancos_deletados}")
    else:
        print("✓ Nenhum banco teste encontrado")
    
    print("\n=== LIMPEZA CONCLUÍDA COM SUCESSO ===")
    print("Todos os dados de teste foram removidos do sistema.")

if __name__ == '__main__':
    try:
        limpar_dados_teste()
    except Exception as e:
        print(f"Erro durante a limpeza: {e}")
        sys.exit(1)