#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Conta, CustomUser

def verificar_tenant_ids():
    print("=== VERIFICAÇÃO DE TENANT IDS ===")
    
    # Verificar usuários
    users = CustomUser.objects.all()
    print(f"\nUsuários encontrados: {len(users)}")
    
    for user in users:
        documento = user.get_documento()
        tenant_id_calculado = hash(documento or user.username) % 1000000
        print(f"  User: {user.username}")
        print(f"    Documento: {documento}")
        print(f"    Tenant ID calculado: {tenant_id_calculado}")
    
    # Verificar contas
    contas = Conta.objects.all()
    print(f"\nContas encontradas: {len(contas)}")
    
    for conta in contas:
        print(f"  ID: {conta.id}, Nome: {conta.nome}, tenant_id: {conta.tenant_id}")
    
    # Verificar compatibilidade
    print("\n=== ANÁLISE DE COMPATIBILIDADE ===")
    user = users.first()
    if user:
        documento = user.get_documento()
        tenant_id_user = hash(documento or user.username) % 1000000
        print(f"Tenant ID do usuário '{user.username}': {tenant_id_user}")
        
        contas_compativeis = Conta.objects.filter(tenant_id=tenant_id_user)
        print(f"Contas compatíveis com este usuário: {len(contas_compativeis)}")
        
        for conta in contas_compativeis:
            print(f"  - {conta.nome} (ID: {conta.id})")

if __name__ == '__main__':
    verificar_tenant_ids()