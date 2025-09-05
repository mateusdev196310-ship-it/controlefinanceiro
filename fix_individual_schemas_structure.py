# -*- coding: utf-8 -*-
from django.db import connection

def fix_individual_schemas_structure():
    print('=== CORRIGINDO ESTRUTURA DOS SCHEMAS INDIVIDUAIS ===')
    
    cursor = connection.cursor()
    
    # Verificar schemas existentes
    cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%';")
    schemas = cursor.fetchall()
    
    if not schemas:
        print('Nenhum schema individual encontrado!')
        return
    
    for schema_tuple in schemas:
        schema_name = schema_tuple[0]
        print(f'\nCorrigindo estrutura do schema: {schema_name}')
        
        try:
            # Definir search_path para o schema individual
            cursor.execute(f'SET search_path TO {schema_name};')
            
            # 1. Corrigir tabela financas_conta
            print('  Corrigindo tabela financas_conta...')
            
            # Verificar se as colunas saldo_inicial e saldo_atual existem
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'financas_conta' 
                AND table_schema = %s
                AND column_name IN ('saldo_inicial', 'saldo_atual', 'saldo');
            """, [schema_name])
            
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            if 'saldo' not in existing_columns and ('saldo_inicial' in existing_columns or 'saldo_atual' in existing_columns):
                # Adicionar coluna saldo
                cursor.execute('ALTER TABLE financas_conta ADD COLUMN IF NOT EXISTS saldo NUMERIC NOT NULL DEFAULT 0.00;')
                
                # Se temos saldo_atual, copiar seus valores para saldo
                if 'saldo_atual' in existing_columns:
                    cursor.execute('UPDATE financas_conta SET saldo = COALESCE(saldo_atual, 0.00);')
                elif 'saldo_inicial' in existing_columns:
                    cursor.execute('UPDATE financas_conta SET saldo = COALESCE(saldo_inicial, 0.00);')
                
                # Remover colunas antigas se existirem
                if 'saldo_inicial' in existing_columns:
                    cursor.execute('ALTER TABLE financas_conta DROP COLUMN IF EXISTS saldo_inicial;')
                if 'saldo_atual' in existing_columns:
                    cursor.execute('ALTER TABLE financas_conta DROP COLUMN IF EXISTS saldo_atual;')
                    
                print('    - Coluna saldo adicionada e colunas antigas removidas')
            
            # Adicionar colunas que podem estar faltando na tabela financas_conta
            missing_conta_columns = [
                ('tipo', 'CHARACTER VARYING(50) NOT NULL DEFAULT \'corrente\''),
                ('cnpj', 'CHARACTER VARYING(18)'),
                ('numero_conta', 'CHARACTER VARYING(20)'),
                ('agencia', 'CHARACTER VARYING(10)')
            ]
            
            for col_name, col_definition in missing_conta_columns:
                cursor.execute(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'financas_conta' 
                    AND table_schema = %s
                    AND column_name = %s;
                """, [schema_name, col_name])
                
                if not cursor.fetchone():
                    cursor.execute(f'ALTER TABLE financas_conta ADD COLUMN {col_name} {col_definition};')
                    print(f'    - Coluna {col_name} adicionada')
            
            # 2. Corrigir tabela financas_transacao
            print('  Corrigindo tabela financas_transacao...')
            
            # Adicionar colunas que podem estar faltando na tabela financas_transacao
            missing_transacao_columns = [
                ('responsavel', 'CHARACTER VARYING(100)'),
                ('eh_parcelada', 'BOOLEAN DEFAULT FALSE'),
                ('transacao_pai_id', 'INTEGER'),
                ('numero_parcela', 'INTEGER'),
                ('total_parcelas', 'INTEGER'),
                ('despesa_parcelada_id', 'INTEGER'),
                ('data_pagamento', 'DATE')
            ]
            
            for col_name, col_definition in missing_transacao_columns:
                cursor.execute(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'financas_transacao' 
                    AND table_schema = %s
                    AND column_name = %s;
                """, [schema_name, col_name])
                
                if not cursor.fetchone():
                    cursor.execute(f'ALTER TABLE financas_transacao ADD COLUMN {col_name} {col_definition};')
                    print(f'    - Coluna {col_name} adicionada')
            
            print(f'  Schema {schema_name} corrigido com sucesso!')
            
        except Exception as e:
            print(f'  Erro ao corrigir {schema_name}: {e}')
    
    print('\n=== VERIFICANDO ESTRUTURAS CORRIGIDAS ===')
    
    # Verificar se as correções foram aplicadas
    for schema_tuple in schemas:
        schema_name = schema_tuple[0]
        
        try:
            cursor.execute(f'SET search_path TO {schema_name};')
            
            # Verificar colunas da tabela financas_conta
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'financas_conta' 
                AND table_schema = %s
                ORDER BY ordinal_position;
            """, [schema_name])
            
            conta_columns = [row[0] for row in cursor.fetchall()]
            print(f'\n{schema_name} - financas_conta: {conta_columns}')
            
            # Verificar colunas da tabela financas_transacao
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'financas_transacao' 
                AND table_schema = %s
                ORDER BY ordinal_position;
            """, [schema_name])
            
            transacao_columns = [row[0] for row in cursor.fetchall()]
            print(f'{schema_name} - financas_transacao: {transacao_columns}')
            
        except Exception as e:
            print(f'Erro ao verificar {schema_name}: {e}')

# Executar a função
fix_individual_schemas_structure()