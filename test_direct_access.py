import os
import sys
import django
from django.test import Client
from django.urls import reverse

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

print("=== TESTE DIRETO COM DJANGO CLIENT ===")

client = Client()

# URLs para testar
urls_to_test = [
    ('dashboard', '/'),
    ('transacoes', '/transacoes/'),
    ('adicionar_transacao', '/adicionar-transacao/'),
    ('adicionar_categoria', '/adicionar-categoria/'),
    ('adicionar_despesa_parcelada', '/adicionar-despesa-parcelada/'),
    ('despesas_parceladas', '/despesas-parceladas/'),
    ('contas', '/contas/'),
    ('relatorios', '/relatorios/')
]

for name, url in urls_to_test:
    try:
        # Testar com reverse
        reversed_url = reverse(name)
        print(f"✓ reverse('{name}') -> {reversed_url}")
        
        # Testar acesso direto
        response = client.get(url)
        print(f"✓ GET {url} -> Status: {response.status_code}")
        
        if response.status_code == 404:
            print(f"  ⚠️  404 Error para {url}")
        elif response.status_code == 200:
            print(f"  ✅ Sucesso para {url}")
        else:
            print(f"  ⚠️  Status inesperado {response.status_code} para {url}")
            
    except Exception as e:
        print(f"✗ Erro com {name} ({url}): {e}")
    
    print()

print("=== TESTE DE RESOLUÇÃO DE URL ===")
from django.urls import resolve

for name, url in urls_to_test:
    try:
        resolved = resolve(url)
        print(f"✓ resolve('{url}') -> {resolved.func.__name__}")
    except Exception as e:
        print(f"✗ Erro ao resolver '{url}': {e}")