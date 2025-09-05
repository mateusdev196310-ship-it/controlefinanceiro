import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

def sync_migrations():
    try:
        cursor = connection.cursor()
        
        # Lista de migrações do financas para marcar como aplicadas
        migrations_to_add = [
            ('financas', '0002_customuser'),
            ('financas', '0003_tenant'),
            ('financas', '0004_add_tenant_id_to_categoria'),
            ('financas', '0005_add_tenant_id_to_conta'),
            ('financas', '0006_add_tenant_id_to_transacao'),
            ('financas', '0007_add_tenant_id_to_despesaparcelada'),
        ]
        
        print("Adicionando registros de migrações...")
        
        for app, migration in migrations_to_add:
            try:
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES (%s, %s, NOW())
                    ON CONFLICT DO NOTHING;
                """, [app, migration])
                print(f"  ✅ {app}.{migration}")
            except Exception as e:
                print(f"  ⚠️ {app}.{migration} - {e}")
        
        # Verificar todas as migrações registradas
        cursor.execute("SELECT app, name FROM django_migrations WHERE app = 'financas' ORDER BY name;")
        financas_migrations = cursor.fetchall()
        
        print(f"\nMigrações do financas registradas: {len(financas_migrations)}")
        for app, name in financas_migrations:
            print(f"  - {app}: {name}")
        
        print("\n🎉 Sincronização de migrações concluída!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    sync_migrations()