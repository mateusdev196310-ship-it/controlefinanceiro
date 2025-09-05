from django.db import connection

def check_schemas():
    cursor = connection.cursor()
    
    # Verificar schemas existentes
    cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'user_%';")
    schemas = cursor.fetchall()
    print(f'Schemas encontrados: {len(schemas)}')
    
    for schema in schemas:
        schema_name = schema[0]
        print(f'\nVerificando schema: {schema_name}')
        
        try:
            # Definir search_path para o schema
            cursor.execute(f'SET search_path TO {schema_name};')
            
            # Verificar transações
            cursor.execute('SELECT COUNT(*) FROM financas_transacao;')
            transacoes = cursor.fetchone()[0]
            
            # Verificar contas
            cursor.execute('SELECT COUNT(*) FROM financas_conta;')
            contas = cursor.fetchone()[0]
            
            # Verificar categorias
            cursor.execute('SELECT COUNT(*) FROM financas_categoria;')
            categorias = cursor.fetchone()[0]
            
            print(f'  Transações: {transacoes}')
            print(f'  Contas: {contas}')
            print(f'  Categorias: {categorias}')
            
        except Exception as e:
            print(f'  Erro ao verificar {schema_name}: {e}')
    
    # Verificar dados no schema público
    print('\nVerificando schema público:')
    cursor.execute('SET search_path TO public;')
    
    cursor.execute('SELECT COUNT(*) FROM financas_transacao;')
    transacoes_public = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM financas_conta;')
    contas_public = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM financas_categoria;')
    categorias_public = cursor.fetchone()[0]
    
    print(f'  Transações: {transacoes_public}')
    print(f'  Contas: {contas_public}')
    print(f'  Categorias: {categorias_public}')
    
    # Verificar distribuição por tenant_id
    cursor.execute('SELECT tenant_id, COUNT(*) FROM financas_transacao GROUP BY tenant_id;')
    tenant_distribution = cursor.fetchall()
    print(f'\nDistribuição por tenant_id:')
    for tenant_id, count in tenant_distribution:
        print(f'  Tenant {tenant_id}: {count} transações')

# Executar a função diretamente
check_schemas()