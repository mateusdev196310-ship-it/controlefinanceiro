# Generated manually to fix SQLite tenant_id issue

from django.db import migrations


def check_and_add_tenant_id(apps, schema_editor):
    """Verifica se a coluna tenant_id existe e, se não existir, a adiciona."""
    # Obter o cursor do banco de dados
    cursor = schema_editor.connection.cursor()
    
    # Verificar se estamos usando SQLite
    if schema_editor.connection.vendor == 'sqlite':
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(financas_fechamentomensal)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Se a coluna não existir, adicioná-la
        if 'tenant_id' not in columns:
            cursor.execute(
                "ALTER TABLE financas_fechamentomensal ADD COLUMN tenant_id integer NULL;"
            )
            cursor.execute(
                "CREATE INDEX financas_fechamentomensal_tenant_id_idx ON financas_fechamentomensal (tenant_id);"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('financas', '0017_add_tenant_id_sqlite'),
    ]

    operations = [
        migrations.RunPython(check_and_add_tenant_id, migrations.RunPython.noop),
    ]