import os
import django
from django.test import Client
from django.http import HttpRequest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.views import despesas_parceladas
from financas.models import DespesaParcelada

# Teste direto da view
print('Testando view despesas_parceladas...')

# Criar um request mock
request = HttpRequest()
request.method = 'GET'

try:
    response = despesas_parceladas(request)
    print(f'Status da resposta: {response.status_code}')
    print(f'Tipo da resposta: {type(response)}')
    if hasattr(response, 'content'):
        print(f'Tamanho do conteúdo: {len(response.content)} bytes')
except Exception as e:
    print(f'Erro na view: {e}')
    import traceback
    traceback.print_exc()

# Teste com Client do Django
print('\nTestando com Django Client...')
client = Client()
try:
    response = client.get('/despesas-parceladas/')
    print(f'Status da resposta: {response.status_code}')
    if response.status_code == 200:
        print('Sucesso!')
    else:
        print(f'Erro: {response.status_code}')
        print(f'Conteúdo: {response.content[:500]}')
except Exception as e:
    print(f'Erro no client: {e}')
    import traceback
    traceback.print_exc()