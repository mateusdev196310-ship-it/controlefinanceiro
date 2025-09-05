import os
import sys
import django
from django.conf import settings
from django.urls import get_resolver

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

print("=== DEBUG DJANGO URLS ===")
print(f"Django version: {django.get_version()}")
print(f"Settings module: {settings.SETTINGS_MODULE}")
print(f"Installed apps: {settings.INSTALLED_APPS}")

print("\n=== URL PATTERNS ===")
resolver = get_resolver()
print(f"Root URLconf: {resolver.url_patterns}")

print("\n=== FINANCAS APP URLS ===")
try:
    from financas.urls import urlpatterns
    print(f"Financas URLs: {len(urlpatterns)} patterns found")
    for i, pattern in enumerate(urlpatterns):
        print(f"{i+1}. {pattern.pattern} -> {pattern.callback}")
except Exception as e:
    print(f"Erro ao importar financas.urls: {e}")

print("\n=== VIEWS DISPONÍVEIS ===")
try:
    from financas import views
    view_functions = [attr for attr in dir(views) if callable(getattr(views, attr)) and not attr.startswith('_')]
    print(f"Views encontradas: {view_functions}")
except Exception as e:
    print(f"Erro ao importar views: {e}")