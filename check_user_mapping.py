# -*- coding: utf-8 -*-
from financas.models import CustomUser
from django.db import connection

def check_user_mapping():
    print('=== MAPEAMENTO DE USUARIOS ===')
    
    # Listar todos os usuarios
    users = CustomUser.objects.all()
    for user in users:
        cpf_cnpj = getattr(user, 'cpf', None) or getattr(user, 'cnpj', None)
        print(f'User ID: {user.id}, Username: {user.username}, CPF/CNPJ: {cpf_cnpj}')
    
    print('\n=== DADOS NO SCHEMA PUBLICO ===')
    cursor = connection.cursor()
    cursor.execute('SET search_path TO public;')
    
    # Verificar transacoes por tenant_id
    cursor.execute('SELECT tenant_id, COUNT(*) FROM financas_transacao GROUP BY tenant_id ORDER BY tenant_id;')
    transacoes = cursor.fetchall()
    print('Transacoes por tenant_id:')
    for tenant_id, count in transacoes:
        print(f'  Tenant {tenant_id}: {count} transacoes')
    
    # Verificar contas por tenant_id
    cursor.execute('SELECT tenant_id, COUNT(*) FROM financas_conta GROUP BY tenant_id ORDER BY tenant_id;')
    contas = cursor.fetchall()
    print('\nContas por tenant_id:')
    for tenant_id, count in contas:
        print(f'  Tenant {tenant_id}: {count} contas')
    
    # Verificar categorias por tenant_id
    cursor.execute('SELECT tenant_id, COUNT(*) FROM financas_categoria GROUP BY tenant_id ORDER BY tenant_id;')
    categorias = cursor.fetchall()
    print('\nCategorias por tenant_id:')
    for tenant_id, count in categorias:
        print(f'  Tenant {tenant_id}: {count} categorias')
    
    print('\n=== SCHEMAS EXISTENTES ===')
    cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%' ORDER BY schema_name;")
    schemas = cursor.fetchall()
    for schema in schemas:
        print(f'  Schema: {schema[0]}')

# Executar a funcao
check_user_mapping()