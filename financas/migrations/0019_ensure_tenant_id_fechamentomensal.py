# Generated manually to ensure tenant_id exists in FechamentoMensal

from django.db import migrations, models


def ensure_tenant_id_exists(apps, schema_editor):
    """Verifica se a coluna tenant_id existe e, se não existir, a adiciona."""
    # Obter o cursor do banco de dados
    cursor = schema_editor.connection.cursor()
    
    # Verificar se estamos usando PostgreSQL
    if schema_editor.connection.vendor == 'postgresql':
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'financas_fechamentomensal' 
            AND column_name = 'tenant_id'
        """)
        column_exists = cursor.fetchone()
        
        # Se a coluna não existir, adicioná-la
        if not column_exists:
            cursor.execute(
                "ALTER TABLE financas_fechamentomensal ADD COLUMN tenant_id integer NULL;"
            )
            cursor.execute(
                "CREATE INDEX financas_fechamentomensal_tenant_id_idx ON financas_fechamentomensal (tenant_id);"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('financas', '0018_fix_tenant_id_sqlite_sync'),
    ]

    operations = [
        # Primeiro, garantir que a coluna exista no PostgreSQL
        migrations.RunPython(ensure_tenant_id_exists, migrations.RunPython.noop),
        
        # Não adicionar o campo novamente, pois ele já existe no modelo
        # A migração 0017_add_tenant_id_sqlite já adicionou o campo
    ]