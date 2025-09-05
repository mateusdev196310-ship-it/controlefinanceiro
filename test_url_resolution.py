import os
import sys
import django
from django.test import Client
from django.urls import reverse, resolve
from django.conf import settings

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

print("=== TESTE DE RESOLUÇÃO DE URLs ===")

# Testar resolução de URLs
urls_to_test = [
    '/',
    '/transacoes/',
    '/adicionar-transacao/',
    '/adicionar-categoria/',
    '/contas/',
    '/relatorios/'
]

for url in urls_to_test:
    try:
        resolved = resolve(url)
        print(f"✓ {url} -> {resolved.func.__name__} (OK)")
    except Exception as e:
        print(f"✗ {url} -> ERRO: {e}")

print("\n=== TESTE COM CLIENT ===")
client = Client()

for url in urls_to_test:
    try:
        response = client.get(url)
        print(f"{url} -> Status: {response.status_code}")
        if response.status_code == 404:
            print(f"  Conteúdo: {response.content.decode()[:100]}...")
    except Exception as e:
        print(f"{url} -> ERRO: {e}")

print("\n=== VERIFICAÇÃO DE TEMPLATES ===")
import os
template_dir = os.path.join(settings.BASE_DIR, 'financas', 'templates', 'financas')
if os.path.exists(template_dir):
    templates = os.listdir(template_dir)
    print(f"Templates encontrados: {templates}")
else:
    print(f"Diretório de templates não encontrado: {template_dir}")