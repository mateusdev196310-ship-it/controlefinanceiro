# -*- coding: utf-8 -*-
from django.db import connection

def check_individual_schema_structure():
    print('=== VERIFICANDO ESTRUTURA DOS SCHEMAS INDIVIDUAIS ===')
    
    cursor = connection.cursor()
    
    # Verificar schemas existentes
    cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%';")
    schemas = cursor.fetchall()
    
    if not schemas:
        print('Nenhum schema individual encontrado!')
        return
    
    # Pegar o primeiro schema para verificar estrutura
    schema_name = schemas[0][0]
    print(f'\nVerificando estrutura do schema: {schema_name}')
    
    try:
        # Definir search_path para o schema individual
        cursor.execute(f'SET search_path TO {schema_name};')
        
        # Verificar estrutura da tabela financas_conta
        print('\n=== ESTRUTURA DA TABELA financas_conta ===')
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'financas_conta' 
            AND table_schema = %s
            ORDER BY ordinal_position;
        """, [schema_name])
        
        columns = cursor.fetchall()
        if columns:
            for col in columns:
                print(f'  {col[0]} - {col[1]} - Nullable: {col[2]} - Default: {col[3]}')
        else:
            print('  Tabela financas_conta não encontrada!')
        
        # Verificar estrutura da tabela financas_transacao
        print('\n=== ESTRUTURA DA TABELA financas_transacao ===')
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'financas_transacao' 
            AND table_schema = %s
            ORDER BY ordinal_position;
        """, [schema_name])
        
        columns = cursor.fetchall()
        if columns:
            for col in columns:
                print(f'  {col[0]} - {col[1]} - Nullable: {col[2]} - Default: {col[3]}')
        else:
            print('  Tabela financas_transacao não encontrada!')
        
        # Verificar estrutura da tabela financas_categoria
        print('\n=== ESTRUTURA DA TABELA financas_categoria ===')
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'financas_categoria' 
            AND table_schema = %s
            ORDER BY ordinal_position;
        """, [schema_name])
        
        columns = cursor.fetchall()
        if columns:
            for col in columns:
                print(f'  {col[0]} - {col[1]} - Nullable: {col[2]} - Default: {col[3]}')
        else:
            print('  Tabela financas_categoria não encontrada!')
            
    except Exception as e:
        print(f'Erro ao verificar estrutura: {e}')
    
    # Comparar com schema público
    print('\n=== COMPARANDO COM SCHEMA PUBLICO ===')
    try:
        cursor.execute('SET search_path TO public;')
        
        print('\n--- ESTRUTURA DA TABELA financas_conta NO SCHEMA PUBLICO ---')
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'financas_conta' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f'  {col[0]} - {col[1]} - Nullable: {col[2]} - Default: {col[3]}')
            
    except Exception as e:
        print(f'Erro ao verificar schema público: {e}')

# Executar a função
check_individual_schema_structure()