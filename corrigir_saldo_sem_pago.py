#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Conta

print("=== CORREÇÃO DO SALDO SEM LÓGICA DE PAGO ===")

# Buscar a conta
conta = Conta.objects.first()
if not conta:
    print("Nenhuma conta encontrada!")
    exit()

print(f"Conta: {conta.nome}")
print(f"Saldo atual: R$ {conta.saldo}")

# Atualizar saldo usando o método corrigido
print("\nAtualizando saldo...")
novo_saldo = conta.atualizar_saldo()

print(f"Novo saldo: R$ {novo_saldo}")
print("\nSaldo atualizado com sucesso!")
print("Agora todas as transações são consideradas, independente do status 'pago'.")