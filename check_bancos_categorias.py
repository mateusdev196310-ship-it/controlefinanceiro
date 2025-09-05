# -*- coding: utf-8 -*-
from django.db import connection

def check_bancos_categorias():
    print('=== VERIFICANDO BANCOS E CATEGORIAS ===')
    
    cursor = connection.cursor()
    
    # Verificar bancos no schema público
    print('\n=== BANCOS NO SCHEMA PUBLICO ===')
    try:
        cursor.execute('SET search_path TO public;')
        cursor.execute('SELECT * FROM financas_banco;')
        bancos = cursor.fetchall()
        
        if bancos:
            print('Bancos encontrados:')
            for banco in bancos:
                print(f'  ID: {banco[0]}, Nome: {banco[1]}')
        else:
            print('Nenhum banco encontrado no schema público!')
            
    except Exception as e:
        print(f'Erro ao verificar bancos: {e}')
    
    # Verificar categorias no schema público
    print('\n=== CATEGORIAS NO SCHEMA PUBLICO ===')
    try:
        cursor.execute('SET search_path TO public;')
        cursor.execute('SELECT id, nome, tipo, tenant_id FROM financas_categoria ORDER BY tenant_id, tipo, nome;')
        categorias = cursor.fetchall()
        
        if categorias:
            print('Categorias encontradas:')
            for cat in categorias:
                print(f'  ID: {cat[0]}, Nome: {cat[1]}, Tipo: {cat[2]}, Tenant: {cat[3]}')
        else:
            print('Nenhuma categoria encontrada no schema público!')
            
    except Exception as e:
        print(f'Erro ao verificar categorias: {e}')
    
    # Verificar bancos nos schemas individuais
    print('\n=== BANCOS NOS SCHEMAS INDIVIDUAIS ===')
    
    # Verificar schemas existentes
    cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%';")
    schemas = cursor.fetchall()
    
    for schema_tuple in schemas:
        schema_name = schema_tuple[0]
        print(f'\n--- Schema: {schema_name} ---')
        
        try:
            cursor.execute(f'SET search_path TO {schema_name};')
            
            # Verificar se a tabela financas_banco existe
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = 'financas_banco';
            """, [schema_name])
            
            if cursor.fetchone():
                cursor.execute('SELECT * FROM financas_banco;')
                bancos_schema = cursor.fetchall()
                
                if bancos_schema:
                    print('  Bancos:')
                    for banco in bancos_schema:
                        print(f'    ID: {banco[0]}, Nome: {banco[1]}')
                else:
                    print('  Nenhum banco encontrado neste schema!')
            else:
                print('  Tabela financas_banco não existe neste schema!')
                
            # Verificar categorias padrão
            cursor.execute('SELECT id, nome, tipo FROM financas_categoria ORDER BY tipo, nome;')
            cats_schema = cursor.fetchall()
            
            if cats_schema:
                print('  Categorias:')
                for cat in cats_schema:
                    print(f'    ID: {cat[0]}, Nome: {cat[1]}, Tipo: {cat[2]}')
            else:
                print('  Nenhuma categoria encontrada neste schema!')
                
        except Exception as e:
            print(f'  Erro ao verificar {schema_name}: {e}')
    
    # Verificar se existem categorias padrão definidas no código
    print('\n=== VERIFICANDO DEFINICOES DE CATEGORIAS PADRAO ===')
    try:
        from financas.models import Categoria
        print('Modelo Categoria importado com sucesso')
        
        # Verificar se há algum método para criar categorias padrão
        if hasattr(Categoria, 'criar_categorias_padrao'):
            print('Método criar_categorias_padrao encontrado!')
        else:
            print('Método criar_categorias_padrao NÃO encontrado!')
            
    except Exception as e:
        print(f'Erro ao importar modelo: {e}')

# Executar a função
check_bancos_categorias()