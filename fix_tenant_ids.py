#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import DespesaParcelada, Transacao, Categoria, Conta, CustomUser
from django.db import connection, transaction

def fix_tenant_ids():
    print("=== CORRIGINDO TENANT IDS ===")
    
    # Verificar usuários disponíveis
    users = CustomUser.objects.all()
    print(f"Usuários encontrados: {users.count()}")
    
    if users.count() == 0:
        print("Nenhum usuário encontrado. Não é possível corrigir tenant_ids.")
        return
    
    # Se há apenas um usuário, usar ele como padrão
    if users.count() == 1:
        default_user = users.first()
        print(f"Usando usuário único como padrão: {default_user.username} (ID: {default_user.id})")
    else:
        # Se há múltiplos usuários, listar e pedir para escolher
        print("\nUsuários disponíveis:")
        for user in users:
            print(f"  ID: {user.id}, Username: {user.username}, Email: {user.email}")
        
        user_id = input("\nDigite o ID do usuário para atribuir aos dados sem tenant_id (ou pressione Enter para usar ID 1): ")
        if not user_id:
            user_id = 1
        else:
            user_id = int(user_id)
        
        try:
            default_user = CustomUser.objects.get(id=user_id)
            print(f"Usando usuário: {default_user.username} (ID: {default_user.id})")
        except CustomUser.DoesNotExist:
            print(f"Usuário com ID {user_id} não encontrado. Usando primeiro usuário disponível.")
            default_user = users.first()
    
    print(f"\nCorrigindo dados para tenant_id: {default_user.id}")
    
    with transaction.atomic():
        # Corrigir DespesaParcelada
        despesas_sem_tenant = DespesaParcelada.objects.filter(tenant_id__isnull=True)
        print(f"\nDespesas parceladas sem tenant_id: {despesas_sem_tenant.count()}")
        
        if despesas_sem_tenant.count() > 0:
            updated = despesas_sem_tenant.update(tenant_id=default_user.id)
            print(f"Despesas parceladas atualizadas: {updated}")
        
        # Corrigir Transacao
        transacoes_sem_tenant = Transacao.objects.filter(tenant_id__isnull=True)
        print(f"\nTransações sem tenant_id: {transacoes_sem_tenant.count()}")
        
        if transacoes_sem_tenant.count() > 0:
            updated = transacoes_sem_tenant.update(tenant_id=default_user.id)
            print(f"Transações atualizadas: {updated}")
        
        # Corrigir Categoria
        categorias_sem_tenant = Categoria.objects.filter(tenant_id__isnull=True)
        print(f"\nCategorias sem tenant_id: {categorias_sem_tenant.count()}")
        
        if categorias_sem_tenant.count() > 0:
            updated = categorias_sem_tenant.update(tenant_id=default_user.id)
            print(f"Categorias atualizadas: {updated}")
        
        # Corrigir Conta
        contas_sem_tenant = Conta.objects.filter(tenant_id__isnull=True)
        print(f"\nContas sem tenant_id: {contas_sem_tenant.count()}")
        
        if contas_sem_tenant.count() > 0:
            updated = contas_sem_tenant.update(tenant_id=default_user.id)
            print(f"Contas atualizadas: {updated}")
    
    print("\n=== CORREÇÃO CONCLUÍDA ===")
    
    # Verificar se a correção funcionou
    print("\n=== VERIFICAÇÃO PÓS-CORREÇÃO ===")
    
    # Simular o tenant_id na conexão para testar o TenantManager
    connection.tenant_id = default_user.id
    
    despesas_visiveis = DespesaParcelada.objects.all()
    print(f"Despesas parceladas visíveis com tenant_id {default_user.id}: {despesas_visiveis.count()}")
    
    for despesa in despesas_visiveis:
        print(f"  Despesa ID: {despesa.id}, Descrição: {despesa.descricao}, Tenant ID: {despesa.tenant_id}")
    
    # Limpar tenant_id da conexão
    if hasattr(connection, 'tenant_id'):
        delattr(connection, 'tenant_id')
    
    print("\n=== VERIFICAÇÃO CONCLUÍDA ===")

if __name__ == '__main__':
    fix_tenant_ids()