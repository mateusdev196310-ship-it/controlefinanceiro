import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.urls import urlpatterns
from django.urls import reverse

print('URLs carregadas:')
for pattern in urlpatterns:
    print(f'  {pattern.pattern} -> {pattern.callback.__name__}')

print('\nTestando reverse das URLs:')
try:
    print('despesas_parceladas:', reverse('despesas_parceladas'))
except Exception as e:
    print('Erro ao fazer reverse de despesas_parceladas:', e)

try:
    print('adicionar_despesa_parcelada:', reverse('adicionar_despesa_parcelada'))
except Exception as e:
    print('Erro ao fazer reverse de adicionar_despesa_parcelada:', e)