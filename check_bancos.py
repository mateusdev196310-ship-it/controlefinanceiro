import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Banco

print('Bancos cadastrados:')
bancos = Banco.objects.all()
if bancos.exists():
    for banco in bancos:
        print(f'{banco.codigo} - {banco.nome}')
else:
    print('Nenhum banco cadastrado no sistema.')