import os
import django
import psycopg2
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser

def check_users_and_schemas():
    print("=== VERIFICANDO USUÁRIOS ATIVOS ===")
    
    # Listar todos os usuários ativos
    users = CustomUser.objects.all()
    print(f"Total de usuários no sistema: {users.count()}")
    
    active_user_ids = []
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, CPF: {user.cpf}")
        active_user_ids.append(user.id)
    
    print("\n=== VERIFICANDO SCHEMAS EXISTENTES ===")
    
    # Conectar ao PostgreSQL para verificar schemas
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            database=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            port=settings.DATABASES['default']['PORT']
        )
        
        cursor = conn.cursor()
        
        # Listar todos os schemas que começam com 'user_'
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'user_%'
            ORDER BY schema_name;
        """)
        
        existing_schemas = cursor.fetchall()
        print(f"Schemas encontrados: {len(existing_schemas)}")
        
        existing_schema_ids = []
        for schema in existing_schemas:
            schema_name = schema[0]
            schema_id = schema_name.replace('user_', '')
            print(f"Schema: {schema_name} (ID: {schema_id})")
            try:
                existing_schema_ids.append(int(schema_id))
            except ValueError:
                print(f"  -> Schema com ID não numérico: {schema_id}")
        
        print("\n=== ANÁLISE ===")
        
        # Verificar quais usuários não têm schema
        missing_schemas = []
        for user_id in active_user_ids:
            if user_id not in existing_schema_ids:
                missing_schemas.append(user_id)
                print(f"❌ Usuário ID {user_id} NÃO tem schema correspondente")
            else:
                print(f"✅ Usuário ID {user_id} tem schema correspondente")
        
        # Verificar quais schemas não têm usuário
        orphan_schemas = []
        for schema_id in existing_schema_ids:
            if schema_id not in active_user_ids:
                orphan_schemas.append(schema_id)
                print(f"⚠️  Schema user_{schema_id} NÃO tem usuário correspondente")
        
        print(f"\n=== RESUMO ===")
        print(f"Usuários ativos: {len(active_user_ids)}")
        print(f"Schemas existentes: {len(existing_schema_ids)}")
        print(f"Usuários sem schema: {len(missing_schemas)} - IDs: {missing_schemas}")
        print(f"Schemas órfãos: {len(orphan_schemas)} - IDs: {orphan_schemas}")
        
        cursor.close()
        conn.close()
        
        return {
            'active_users': active_user_ids,
            'existing_schemas': existing_schema_ids,
            'missing_schemas': missing_schemas,
            'orphan_schemas': orphan_schemas
        }
        
    except Exception as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

if __name__ == "__main__":
    result = check_users_and_schemas()
    
    if result and result['missing_schemas']:
        print("\n⚠️  AÇÃO NECESSÁRIA: Alguns usuários não têm schemas correspondentes!")
        print("Execute o script de criação de schemas para corrigir isso.")
    elif result and not result['missing_schemas']:
        print("\n✅ Todos os usuários ativos têm schemas correspondentes.")