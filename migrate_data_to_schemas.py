# -*- coding: utf-8 -*-
"""
Script para migrar dados do schema público para os schemas individuais baseados em CPF/CNPJ.
"""

from django.contrib.auth import get_user_model
from django.db import connection
from financas.models import Transacao, Conta, Categoria, Banco

User = get_user_model()

def sanitize_schema_name(cpf_cnpj):
    """Sanitiza CPF/CNPJ para usar como nome de schema"""
    if not cpf_cnpj:
        return None
    import re
    # Remove pontos, traços e barras
    clean = re.sub(r'[.\-/]', '', str(cpf_cnpj))
    # Adiciona prefixo para garantir que comece com letra
    return f"user_{clean}"

def migrate_data_to_schemas():
    print("=== MIGRACAO DE DADOS PARA SCHEMAS INDIVIDUAIS ===")
    print()
    
    # 1. Mapear usuários para seus schemas
    print("1. MAPEANDO USUARIOS PARA SCHEMAS:")
    user_schema_map = {}
    
    users = User.objects.all()
    for user in users:
        cpf_cnpj = user.cpf or user.cnpj or f"id_{user.id}"
        schema_name = sanitize_schema_name(cpf_cnpj)
        user_schema_map[user.id] = schema_name
        print(f"   Usuario {user.username} (ID: {user.id}) -> Schema: {schema_name}")
    
    print()
    
    # 2. Verificar dados no schema público
    print("2. DADOS NO SCHEMA PUBLICO:")
    
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public")
        
        # Contar dados por tenant_id
        cursor.execute("""
            SELECT tenant_id, COUNT(*) 
            FROM financas_transacao 
            WHERE tenant_id IS NOT NULL 
            GROUP BY tenant_id
        """)
        transacoes_por_tenant = cursor.fetchall()
        
        cursor.execute("""
            SELECT tenant_id, COUNT(*) 
            FROM financas_conta 
            WHERE tenant_id IS NOT NULL 
            GROUP BY tenant_id
        """)
        contas_por_tenant = cursor.fetchall()
        
        cursor.execute("""
            SELECT tenant_id, COUNT(*) 
            FROM financas_categoria 
            WHERE tenant_id IS NOT NULL 
            GROUP BY tenant_id
        """)
        categorias_por_tenant = cursor.fetchall()
        
        print("   Transacoes por tenant_id:")
        for tenant_id, count in transacoes_por_tenant:
            schema_name = user_schema_map.get(tenant_id, f"user_{tenant_id}")
            print(f"     tenant_id {tenant_id} ({schema_name}): {count} transacoes")
        
        print("   Contas por tenant_id:")
        for tenant_id, count in contas_por_tenant:
            schema_name = user_schema_map.get(tenant_id, f"user_{tenant_id}")
            print(f"     tenant_id {tenant_id} ({schema_name}): {count} contas")
        
        print("   Categorias por tenant_id:")
        for tenant_id, count in categorias_por_tenant:
            schema_name = user_schema_map.get(tenant_id, f"user_{tenant_id}")
            print(f"     tenant_id {tenant_id} ({schema_name}): {count} categorias")
    
    print()
    
    # 3. Migrar dados para schemas individuais
    print("3. MIGRANDO DADOS PARA SCHEMAS INDIVIDUAIS:")
    
    for tenant_id, schema_name in user_schema_map.items():
        print(f"   Migrando dados do tenant_id {tenant_id} para schema {schema_name}...")
        
        try:
            with connection.cursor() as cursor:
                # Verificar se o schema existe
                cursor.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = %s
                """, [schema_name])
                
                if not cursor.fetchone():
                    print(f"     ERRO: Schema {schema_name} não existe!")
                    continue
                
                # Migrar categorias
                cursor.execute("SET search_path TO public")
                cursor.execute("""
                    SELECT id, nome, cor, tipo, tenant_id
                    FROM financas_categoria 
                    WHERE tenant_id = %s
                """, [tenant_id])
                categorias = cursor.fetchall()
                
                if categorias:
                    cursor.execute(f"SET search_path TO {schema_name}")
                    for cat_id, nome, cor, tipo, t_id in categorias:
                        # Verificar se já existe
                        cursor.execute("""
                            SELECT id FROM financas_categoria WHERE nome = %s
                        """, [nome])
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT INTO financas_categoria (nome, cor, tipo, tenant_id)
                                VALUES (%s, %s, %s, %s)
                            """, [nome, cor, tipo, t_id])
                    print(f"     Migradas {len(categorias)} categorias")
                
                # Migrar contas
                cursor.execute("SET search_path TO public")
                cursor.execute("""
                    SELECT id, nome, saldo, cor, tipo, banco_id, cnpj, numero_conta, agencia, tenant_id
                    FROM financas_conta 
                    WHERE tenant_id = %s
                """, [tenant_id])
                contas = cursor.fetchall()
                
                if contas:
                    cursor.execute(f"SET search_path TO {schema_name}")
                    conta_id_map = {}  # Mapear IDs antigos para novos
                    
                    for conta_data in contas:
                        old_id, nome, saldo, cor, tipo, banco_id, cnpj, numero_conta, agencia, t_id = conta_data
                        
                        # Verificar se já existe
                        cursor.execute("""
                            SELECT id FROM financas_conta WHERE nome = %s AND tenant_id = %s
                        """, [nome, t_id])
                        existing = cursor.fetchone()
                        
                        if not existing:
                            cursor.execute("""
                                INSERT INTO financas_conta (nome, saldo, cor, tipo, banco_id, cnpj, numero_conta, agencia, tenant_id)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                RETURNING id
                            """, [nome, saldo, cor, tipo, banco_id, cnpj, numero_conta, agencia, t_id])
                            new_id = cursor.fetchone()[0]
                            conta_id_map[old_id] = new_id
                        else:
                            conta_id_map[old_id] = existing[0]
                    
                    print(f"     Migradas {len(contas)} contas")
                
                # Migrar transações
                cursor.execute("SET search_path TO public")
                cursor.execute("""
                    SELECT t.id, t.data, t.descricao, t.valor, t.categoria_id, t.tipo, t.responsavel, 
                           t.eh_parcelada, t.transacao_pai_id, t.numero_parcela, t.total_parcelas, 
                           t.conta_id, t.despesa_parcelada_id, t.pago, t.data_pagamento, t.tenant_id,
                           c.nome as categoria_nome
                    FROM financas_transacao t
                    JOIN financas_categoria c ON t.categoria_id = c.id
                    WHERE t.tenant_id = %s
                """, [tenant_id])
                transacoes = cursor.fetchall()
                
                if transacoes:
                    cursor.execute(f"SET search_path TO {schema_name}")
                    
                    for trans_data in transacoes:
                        (old_id, data, descricao, valor, old_cat_id, tipo, responsavel, 
                         eh_parcelada, transacao_pai_id, numero_parcela, total_parcelas, 
                         old_conta_id, despesa_parcelada_id, pago, data_pagamento, t_id, categoria_nome) = trans_data
                        
                        # Buscar nova categoria_id
                        cursor.execute("""
                            SELECT id FROM financas_categoria WHERE nome = %s
                        """, [categoria_nome])
                        new_cat_result = cursor.fetchone()
                        if not new_cat_result:
                            print(f"       AVISO: Categoria '{categoria_nome}' não encontrada no schema {schema_name}")
                            continue
                        new_cat_id = new_cat_result[0]
                        
                        # Buscar nova conta_id
                        new_conta_id = conta_id_map.get(old_conta_id)
                        if not new_conta_id:
                            print(f"       AVISO: Conta ID {old_conta_id} não encontrada no mapeamento")
                            continue
                        
                        # Verificar se transação já existe
                        cursor.execute("""
                            SELECT id FROM financas_transacao 
                            WHERE descricao = %s AND valor = %s AND data = %s AND tenant_id = %s
                        """, [descricao, valor, data, t_id])
                        
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT INTO financas_transacao 
                                (data, descricao, valor, categoria_id, tipo, responsavel, eh_parcelada, 
                                 transacao_pai_id, numero_parcela, total_parcelas, conta_id, 
                                 despesa_parcelada_id, pago, data_pagamento, tenant_id)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, [data, descricao, valor, new_cat_id, tipo, responsavel, eh_parcelada,
                                  None, numero_parcela, total_parcelas, new_conta_id,
                                  None, pago, data_pagamento, t_id])
                    
                    print(f"     Migradas {len(transacoes)} transacoes")
                
        except Exception as e:
            print(f"     ERRO ao migrar dados para {schema_name}: {e}")
    
    print()
    
    # 4. Verificar migração
    print("4. VERIFICANDO MIGRACAO:")
    
    for tenant_id, schema_name in user_schema_map.items():
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema_name}")
                
                cursor.execute("SELECT COUNT(*) FROM financas_transacao")
                transacoes = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM financas_conta")
                contas = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM financas_categoria")
                categorias = cursor.fetchone()[0]
                
                print(f"   Schema {schema_name}: {transacoes} transacoes, {contas} contas, {categorias} categorias")
                
        except Exception as e:
            print(f"   ERRO ao verificar {schema_name}: {e}")
    
    print()
    print("=== MIGRACAO CONCLUIDA ===")

if __name__ == '__main__':
    migrate_data_to_schemas()