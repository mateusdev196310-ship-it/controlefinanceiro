import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def fix_migration_dependency():
    try:
        cursor = connection.cursor()
        
        # Inserir o registro da migração inicial do financas
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied) 
            VALUES ('financas', '0001_initial', NOW())
            ON CONFLICT DO NOTHING;
        """)
        
        print("✅ Registro da migração financas.0001_initial adicionado")
        
        # Verificar todas as migrações
        cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, name;")
        migrations = cursor.fetchall()
        
        print(f"\nMigrações registradas: {len(migrations)}")
        for app, name in migrations:
            print(f"  - {app}: {name}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    fix_migration_dependency()