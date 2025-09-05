# -*- coding: utf-8 -*-
"""
Script para debugar o sistema de tenant e verificar por que os schemas individuais estao vazios.
"""

from django.contrib.auth import get_user_model
from django.db import connection
from financas.models import Transacao, Conta, Categoria, Banco
from financas.middleware import TenantMiddleware
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

def debug_tenant_system():
    print("=== DEBUG DO SISTEMA DE TENANT ===")
    print()
    
    # 1. Verificar usuarios e seus CPF/CNPJ
    print("1. USUARIOS E SEUS DOCUMENTOS:")
    users = User.objects.all()
    for user in users:
        cpf_cnpj = user.cpf or user.cnpj or f"id_{user.id}"
        print(f"   Usuario: {user.username} (ID: {user.id})")
        print(f"   CPF: {user.cpf}")
        print(f"   CNPJ: {user.cnpj}")
        print(f"   Documento usado: {cpf_cnpj}")
        print()
    
    # 2. Verificar dados nos schemas individuais
    print("2. DADOS NOS SCHEMAS INDIVIDUAIS:")
    schemas = ['user_12345678901', 'user_12345678000190', 'user_41159825009', 'user_07761784582']
    
    for schema in schemas:
        print(f"   Schema: {schema}")
        try:
            with connection.cursor() as cursor:
                # Definir search_path para o schema individual
                cursor.execute(f"SET search_path TO {schema}")
                
                # Contar registros nas tabelas
                cursor.execute("SELECT COUNT(*) FROM financas_transacao")
                transacoes = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM financas_conta")
                contas = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM financas_categoria")
                categorias = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM financas_banco")
                bancos = cursor.fetchone()[0]
                
                print(f"     Transacoes: {transacoes}")
                print(f"     Contas: {contas}")
                print(f"     Categorias: {categorias}")
                print(f"     Bancos: {bancos}")
                
                # Verificar views
                try:
                    cursor.execute("SELECT COUNT(*) FROM v_transacoes_completas")
                    view_transacoes = cursor.fetchone()[0]
                    print(f"     View Transacoes Completas: {view_transacoes}")
                except Exception as e:
                    print(f"     View Transacoes Completas: ERRO - {e}")
                
        except Exception as e:
            print(f"     ERRO ao acessar schema: {e}")
        
        print()
    
    # 3. Verificar dados no schema public com tenant_id
    print("3. DADOS NO SCHEMA PUBLIC POR TENANT_ID:")
    
    # Resetar search_path para public
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public")
        
        # Verificar distribuicao por tenant_id
        cursor.execute("""
            SELECT u.username, u.id, COUNT(t.id) as transacoes
            FROM auth_user u
            LEFT JOIN financas_transacao t ON t.tenant_id = u.id
            GROUP BY u.id, u.username
            ORDER BY u.id
        """)
        
        resultados = cursor.fetchall()
        for username, user_id, count in resultados:
            print(f"   Usuario {username} (ID: {user_id}): {count} transacoes")
    
    print()
    
    # 4. Verificar se o problema esta na migracao de dados
    print("4. VERIFICANDO MIGRACAO DE DADOS:")
    
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public")
        
        # Verificar se existem dados sem tenant_id
        cursor.execute("SELECT COUNT(*) FROM financas_transacao WHERE tenant_id IS NULL")
        transacoes_sem_tenant = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM financas_conta WHERE tenant_id IS NULL")
        contas_sem_tenant = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM financas_categoria WHERE tenant_id IS NULL")
        categorias_sem_tenant = cursor.fetchone()[0]
        
        print(f"   Transacoes sem tenant_id: {transacoes_sem_tenant}")
        print(f"   Contas sem tenant_id: {contas_sem_tenant}")
        print(f"   Categorias sem tenant_id: {categorias_sem_tenant}")
        
        # Verificar se os dados foram copiados para os schemas individuais
        print("\n   Verificando se dados foram copiados para schemas individuais...")
        
        for schema in schemas:
            try:
                cursor.execute(f"SET search_path TO {schema}")
                cursor.execute("SELECT COUNT(*) FROM financas_transacao")
                count = cursor.fetchone()[0]
                print(f"   Schema {schema}: {count} transacoes")
            except Exception as e:
                print(f"   Schema {schema}: ERRO - {e}")
    
    print()
    print("=== FIM DO DEBUG ===")

if __name__ == '__main__':
    debug_tenant_system()