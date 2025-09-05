# -*- coding: utf-8 -*-
from django.db import connection

def create_default_categories_for_users():
    print('=== CRIANDO CATEGORIAS PADRAO PARA USUARIOS ===')
    
    cursor = connection.cursor()
    
    # Definir categorias padrão
    categorias_padrao = [
        # Receitas
        {'nome': 'Salário', 'cor': '#28a745', 'tipo': 'receita'},
        {'nome': 'Freelance', 'cor': '#17a2b8', 'tipo': 'receita'},
        {'nome': 'Investimentos', 'cor': '#ffc107', 'tipo': 'receita'},
        {'nome': 'Outros Rendimentos', 'cor': '#20c997', 'tipo': 'receita'},
        
        # Despesas Essenciais
        {'nome': 'Alimentação', 'cor': '#fd7e14', 'tipo': 'despesa'},
        {'nome': 'Transporte', 'cor': '#6f42c1', 'tipo': 'despesa'},
        {'nome': 'Moradia', 'cor': '#e83e8c', 'tipo': 'despesa'},
        {'nome': 'Saúde', 'cor': '#dc3545', 'tipo': 'despesa'},
        {'nome': 'Educação', 'cor': '#20c997', 'tipo': 'despesa'},
        
        # Despesas Variáveis
        {'nome': 'Lazer', 'cor': '#6610f2', 'tipo': 'despesa'},
        {'nome': 'Compras', 'cor': '#fd7e14', 'tipo': 'despesa'},
        {'nome': 'Serviços', 'cor': '#6c757d', 'tipo': 'despesa'},
        {'nome': 'Outros Gastos', 'cor': '#6c757d', 'tipo': 'despesa'},
    ]
    
    # Verificar schemas existentes
    cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%';")
    schemas = cursor.fetchall()
    
    if not schemas:
        print('Nenhum schema individual encontrado!')
        return
    
    for schema_tuple in schemas:
        schema_name = schema_tuple[0]
        print(f'\nCriando categorias padrão para schema: {schema_name}')
        
        try:
            # Definir search_path para o schema individual
            cursor.execute(f'SET search_path TO {schema_name};')
            
            # Verificar categorias existentes
            cursor.execute('SELECT nome FROM financas_categoria;')
            categorias_existentes = [row[0] for row in cursor.fetchall()]
            
            criadas = 0
            existentes = 0
            
            for categoria_data in categorias_padrao:
                nome = categoria_data['nome']
                
                if nome not in categorias_existentes:
                    # Inserir nova categoria
                    cursor.execute(
                        'INSERT INTO financas_categoria (nome, cor, tipo, tenant_id) VALUES (%s, %s, %s, %s);',
                        [nome, categoria_data['cor'], categoria_data['tipo'], 1]  # tenant_id = 1 para schema individual
                    )
                    criadas += 1
                    print(f'  ✓ Categoria "{nome}" criada')
                else:
                    existentes += 1
                    print(f'  ⚠ Categoria "{nome}" já existe')
            
            print(f'  Resumo: {criadas} criadas, {existentes} já existiam')
            
        except Exception as e:
            print(f'  Erro ao criar categorias para {schema_name}: {e}')
    
    print('\n=== VERIFICANDO CATEGORIAS CRIADAS ===')
    
    # Verificar categorias criadas
    for schema_tuple in schemas:
        schema_name = schema_tuple[0]
        
        try:
            cursor.execute(f'SET search_path TO {schema_name};')
            cursor.execute('SELECT COUNT(*) FROM financas_categoria;')
            total_categorias = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM financas_categoria WHERE tipo = \'receita\';')
            total_receitas = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM financas_categoria WHERE tipo = \'despesa\';')
            total_despesas = cursor.fetchone()[0]
            
            print(f'{schema_name}: {total_categorias} categorias ({total_receitas} receitas, {total_despesas} despesas)')
            
        except Exception as e:
            print(f'Erro ao verificar {schema_name}: {e}')

# Executar a função
create_default_categories_for_users()