# -*- coding: utf-8 -*-
from django.db import connection

def check_table_structure():
    cursor = connection.cursor()
    cursor.execute('SET search_path TO public;')
    
    # Verificar estrutura da tabela financas_conta
    print('=== ESTRUTURA DA TABELA financas_conta ===')
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'financas_conta' 
        AND table_schema = 'public'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    for col in columns:
        print(f'  {col[0]} ({col[1]}) - Nullable: {col[2]}')
    
    # Verificar dados reais da tabela
    print('\n=== DADOS DA TABELA financas_conta ===')
    cursor.execute('SELECT * FROM financas_conta LIMIT 3;')
    contas = cursor.fetchall()
    
    if contas:
        print('Primeiras 3 contas:')
        for conta in contas:
            print(f'  {conta}')
    else:
        print('Nenhuma conta encontrada')
    
    # Verificar estrutura da tabela financas_transacao
    print('\n=== ESTRUTURA DA TABELA financas_transacao ===')
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'financas_transacao' 
        AND table_schema = 'public'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    for col in columns:
        print(f'  {col[0]} ({col[1]}) - Nullable: {col[2]}')

# Executar a funcao
check_table_structure()