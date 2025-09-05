# -*- coding: utf-8 -*-
from django.db import connection
from financas.models import CustomUser

def fix_data_migration():
    print('=== CORRIGINDO MIGRACAO DE DADOS ===')
    
    cursor = connection.cursor()
    
    # Mapear usuarios para seus CPF/CNPJ
    users = CustomUser.objects.all()
    user_mapping = {}
    
    for user in users:
        cpf_cnpj = getattr(user, 'cpf', None) or getattr(user, 'cnpj', None)
        if cpf_cnpj:
            # Remover pontuacao do CPF/CNPJ
            clean_cpf_cnpj = cpf_cnpj.replace('.', '').replace('-', '').replace('/', '')
            user_mapping[user.id] = clean_cpf_cnpj
            print(f'User ID {user.id} ({user.username}) -> Schema user_{clean_cpf_cnpj}')
    
    print('\n=== MIGRANDO DADOS PARA SCHEMAS INDIVIDUAIS ===')
    
    # Para cada usuario, migrar seus dados
    for user_id, clean_cpf_cnpj in user_mapping.items():
        schema_name = f'user_{clean_cpf_cnpj}'
        
        print(f'\nMigrando dados do tenant_id {user_id} para schema {schema_name}:')
        
        try:
            # Verificar se o schema existe
            cursor.execute(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}';")
            if not cursor.fetchone():
                print(f'  Schema {schema_name} nao existe, pulando...')
                continue
            
            # Definir search_path para o schema individual
            cursor.execute(f'SET search_path TO {schema_name};')
            
            # Migrar categorias
            cursor.execute('SET search_path TO public;')
            cursor.execute('SELECT id, nome, tipo, tenant_id FROM financas_categoria WHERE tenant_id = %s;', [user_id])
            categorias = cursor.fetchall()
            
            if categorias:
                cursor.execute(f'SET search_path TO {schema_name};')
                # Limpar categorias existentes
                cursor.execute('DELETE FROM financas_categoria;')
                
                for categoria in categorias:
                    cursor.execute(
                        'INSERT INTO financas_categoria (id, nome, tipo, tenant_id) VALUES (%s, %s, %s, %s);',
                        categoria
                    )
                print(f'  Migradas {len(categorias)} categorias')
            
            # Migrar contas
            cursor.execute('SET search_path TO public;')
            cursor.execute('SELECT id, nome, saldo, banco_id, cor, tipo, tenant_id, cnpj, numero_conta, agencia FROM financas_conta WHERE tenant_id = %s;', [user_id])
            contas = cursor.fetchall()
            
            if contas:
                cursor.execute(f'SET search_path TO {schema_name};')
                # Limpar contas existentes
                cursor.execute('DELETE FROM financas_conta;')
                
                for conta in contas:
                    cursor.execute(
                        'INSERT INTO financas_conta (id, nome, saldo, banco_id, cor, tipo, tenant_id, cnpj, numero_conta, agencia) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);',
                        conta
                    )
                print(f'  Migradas {len(contas)} contas')
            else:
                print(f'  Nenhuma conta encontrada para tenant_id {user_id}')
            
            # Migrar transacoes
            cursor.execute('SET search_path TO public;')
            cursor.execute('SELECT id, descricao, valor, data, tipo, conta_id, categoria_id, tenant_id, responsavel, eh_parcelada, transacao_pai_id, numero_parcela, total_parcelas, despesa_parcelada_id, pago, data_pagamento FROM financas_transacao WHERE tenant_id = %s;', [user_id])
            transacoes = cursor.fetchall()
            
            if transacoes:
                cursor.execute(f'SET search_path TO {schema_name};')
                # Limpar transacoes existentes
                cursor.execute('DELETE FROM financas_transacao;')
                
                for transacao in transacoes:
                    cursor.execute(
                        'INSERT INTO financas_transacao (id, descricao, valor, data, tipo, conta_id, categoria_id, tenant_id, responsavel, eh_parcelada, transacao_pai_id, numero_parcela, total_parcelas, despesa_parcelada_id, pago, data_pagamento) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);',
                        transacao
                    )
                print(f'  Migradas {len(transacoes)} transacoes')
            
        except Exception as e:
            print(f'  Erro ao migrar para {schema_name}: {e}')
    
    print('\n=== VERIFICANDO MIGRACAO ===')
    
    # Verificar dados migrados
    for user_id, clean_cpf_cnpj in user_mapping.items():
        schema_name = f'user_{clean_cpf_cnpj}'
        
        try:
            cursor.execute(f'SET search_path TO {schema_name};')
            
            cursor.execute('SELECT COUNT(*) FROM financas_categoria;')
            cat_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM financas_conta;')
            conta_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM financas_transacao;')
            trans_count = cursor.fetchone()[0]
            
            print(f'Schema {schema_name}: {cat_count} categorias, {conta_count} contas, {trans_count} transacoes')
            
        except Exception as e:
            print(f'Erro ao verificar {schema_name}: {e}')

# Executar a funcao
fix_data_migration()