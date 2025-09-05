# -*- coding: utf-8 -*-
"""
Script para verificar se a migração de dados funcionou corretamente.
"""

from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

def verify_migration():
    print("=== VERIFICACAO POS-MIGRACAO ===")
    print()
    
    # Verificar schemas individuais
    schemas_to_check = [
        'user_12345678901',
        'user_12345678000190', 
        'user_41159825009',
        'user_07761784582'
    ]
    
    for schema_name in schemas_to_check:
        print(f"Schema: {schema_name}")
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema_name}")
                
                cursor.execute("SELECT COUNT(*) FROM financas_transacao")
                transacoes = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM financas_conta")
                contas = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM financas_categoria")
                categorias = cursor.fetchone()[0]
                
                print(f"  Transacoes: {transacoes}")
                print(f"  Contas: {contas}")
                print(f"  Categorias: {categorias}")
                
                if transacoes > 0:
                    print("  ✓ MIGRACAO FUNCIONOU!")
                else:
                    print("  ✗ Sem transacoes migradas")
                    
        except Exception as e:
            print(f"  ERRO: {e}")
        
        print()
    
    print("=== VERIFICACAO CONCLUIDA ===")

if __name__ == '__main__':
    verify_migration()