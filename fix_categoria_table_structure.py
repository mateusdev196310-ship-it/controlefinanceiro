# -*- coding: utf-8 -*-
from django.db import connection

def fix_categoria_table_structure():
    print('=== CORRIGINDO ESTRUTURA DA TABELA FINANCAS_CATEGORIA ===')
    
    cursor = connection.cursor()
    
    # Verificar schemas existentes
    cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%';")
    schemas = cursor.fetchall()
    
    if not schemas:
        print('Nenhum schema individual encontrado!')
        return
    
    for schema_tuple in schemas:
        schema_name = schema_tuple[0]
        print(f'\nCorrigindo tabela financas_categoria no schema: {schema_name}')
        
        try:
            # Definir search_path para o schema individual
            cursor.execute(f'SET search_path TO {schema_name};')
            
            # Verificar estrutura atual
            cursor.execute("""
                SELECT column_name, ordinal_position 
                FROM information_schema.columns 
                WHERE table_name = 'financas_categoria' 
                AND table_schema = %s
                ORDER BY ordinal_position;
            """, [schema_name])
            
            columns = cursor.fetchall()
            print(f'  Colunas atuais: {[col[0] for col in columns]}')
            
            # Verificar se há colunas duplicadas
            column_names = [col[0] for col in columns]
            duplicates = [col for col in set(column_names) if column_names.count(col) > 1]
            
            if duplicates:
                print(f'  Colunas duplicadas encontradas: {duplicates}')
                
                # Recriar a tabela com estrutura correta
                print('  Recriando tabela com estrutura correta...')
                
                # Backup dos dados existentes
                cursor.execute('SELECT id, nome, tipo, tenant_id FROM financas_categoria;')
                dados_backup = cursor.fetchall()
                
                # Dropar tabela existente
                cursor.execute('DROP TABLE IF EXISTS financas_categoria CASCADE;')
                
                # Criar tabela com estrutura correta
                cursor.execute("""
                    CREATE TABLE financas_categoria (
                        id SERIAL PRIMARY KEY,
                        nome CHARACTER VARYING(100) NOT NULL,
                        cor CHARACTER VARYING(20) DEFAULT '#6c757d',
                        tipo CHARACTER VARYING(10) DEFAULT 'ambos',
                        tenant_id INTEGER
                    );
                """)
                
                # Restaurar dados
                if dados_backup:
                    for dados in dados_backup:
                        cursor.execute(
                            'INSERT INTO financas_categoria (id, nome, tipo, tenant_id, cor) VALUES (%s, %s, %s, %s, %s);',
                            [dados[0], dados[1], dados[2], dados[3], '#6c757d']
                        )
                    
                    print(f'  Dados restaurados: {len(dados_backup)} registros')
                
                print('  Tabela recriada com sucesso!')
            else:
                print('  Estrutura da tabela está correta')
                
                # Verificar se a coluna cor existe e tem valor padrão
                cursor.execute("""
                    SELECT column_name, column_default 
                    FROM information_schema.columns 
                    WHERE table_name = 'financas_categoria' 
                    AND table_schema = %s
                    AND column_name = 'cor';
                """, [schema_name])
                
                cor_info = cursor.fetchone()
                if not cor_info:
                    # Adicionar coluna cor se não existir
                    cursor.execute('ALTER TABLE financas_categoria ADD COLUMN cor CHARACTER VARYING(20) DEFAULT \'#6c757d\';')
                    print('  Coluna cor adicionada')
                elif not cor_info[1]:  # Se não tem valor padrão
                    # Atualizar registros sem cor
                    cursor.execute('UPDATE financas_categoria SET cor = \'#6c757d\' WHERE cor IS NULL OR cor = \'\';')
                    print('  Valores padrão de cor atualizados')
            
        except Exception as e:
            print(f'  Erro ao corrigir {schema_name}: {e}')
    
    print('\n=== VERIFICANDO ESTRUTURAS CORRIGIDAS ===')
    
    # Verificar estruturas finais
    for schema_tuple in schemas:
        schema_name = schema_tuple[0]
        
        try:
            cursor.execute(f'SET search_path TO {schema_name};')
            
            cursor.execute("""
                SELECT column_name, data_type, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'financas_categoria' 
                AND table_schema = %s
                ORDER BY ordinal_position;
            """, [schema_name])
            
            columns = cursor.fetchall()
            print(f'\n{schema_name} - financas_categoria:')
            for col in columns:
                print(f'  {col[0]} ({col[1]}) - Default: {col[2]}')
                
        except Exception as e:
            print(f'Erro ao verificar {schema_name}: {e}')

# Executar a função
fix_categoria_table_structure()