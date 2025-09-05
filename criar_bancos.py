import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Banco

# Lista de bancos principais do Brasil
bancos_brasil = [
    {'codigo': '001', 'nome': 'Banco do Brasil'},
    {'codigo': '033', 'nome': 'Santander'},
    {'codigo': '104', 'nome': 'Caixa Econômica Federal'},
    {'codigo': '237', 'nome': 'Bradesco'},
    {'codigo': '341', 'nome': 'Itaú'},
    {'codigo': '260', 'nome': 'Nu Pagamentos (Nubank)'},
    {'codigo': '077', 'nome': 'Banco Inter'},
    {'codigo': '212', 'nome': 'Banco Original'},
    {'codigo': '290', 'nome': 'PagSeguro'},
    {'codigo': '323', 'nome': 'Mercado Pago'},
    {'codigo': '336', 'nome': 'C6 Bank'},
    {'codigo': '655', 'nome': 'Banco Votorantim'},
    {'codigo': '422', 'nome': 'Banco Safra'},
    {'codigo': '070', 'nome': 'BRB - Banco de Brasília'},
    {'codigo': '756', 'nome': 'Banco Cooperativo do Brasil (Bancoob)'},
]

print('Criando bancos...')
for banco_data in bancos_brasil:
    banco, created = Banco.objects.get_or_create(
        codigo=banco_data['codigo'],
        defaults={'nome': banco_data['nome']}
    )
    if created:
        print(f'✓ Criado: {banco.codigo} - {banco.nome}')
    else:
        print(f'- Já existe: {banco.codigo} - {banco.nome}')

print(f'\nTotal de bancos cadastrados: {Banco.objects.count()}')