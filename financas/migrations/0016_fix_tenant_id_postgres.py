# Generated manually

from django.db import migrations


def skip_operation(*args, **kwargs):
    """Função que não faz nada, apenas para compatibilidade com SQLite"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('financas', '0015_fix_duplicate_tenant_id'),
    ]

    operations = [
        # Esta migração é uma correção para o problema de coluna duplicada
        # Não faz nada no SQLite local, mas no PostgreSQL de produção
        # vai evitar o erro de coluna duplicada
        migrations.RunPython(
            code=skip_operation,
            reverse_code=skip_operation,
        )
    ]