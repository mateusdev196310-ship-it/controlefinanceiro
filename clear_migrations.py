import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection

def clear_financas_migrations():
    try:
        cursor = connection.cursor()
        
        # Remover registros de migrações do app financas
        cursor.execute("DELETE FROM django_migrations WHERE app = 'financas';")
        deleted_count = cursor.rowcount
        
        print(f"✅ {deleted_count} registros de migração do app 'financas' removidos")
        
        # Verificar migrações restantes
        cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, name;")
        remaining = cursor.fetchall()
        
        print(f"\nMigrações restantes no registro: {len(remaining)}")
        for app, name in remaining:
            print(f"  - {app}: {name}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    clear_financas_migrations()