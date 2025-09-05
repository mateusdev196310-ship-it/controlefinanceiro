import os
import sys
import django
from django.conf import settings

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

print("=== TESTE DE IMPORTAÇÃO DE VIEWS ===")

try:
    from financas.views import (
        dashboard,
        transacoes,
        adicionar_transacao,
        adicionar_categoria,
        adicionar_despesa_parcelada,
        despesas_parceladas,
        detalhes_despesa_parcelada,
        contas,
        relatorios
    )
    print("✓ Todas as views foram importadas com sucesso!")
    
    # Testar se as funções são chamáveis
    views_to_test = {
        'dashboard': dashboard,
        'transacoes': transacoes,
        'adicionar_transacao': adicionar_transacao,
        'adicionar_categoria': adicionar_categoria,
        'adicionar_despesa_parcelada': adicionar_despesa_parcelada,
        'despesas_parceladas': despesas_parceladas,
        'detalhes_despesa_parcelada': detalhes_despesa_parcelada,
        'contas': contas,
        'relatorios': relatorios
    }
    
    for name, view_func in views_to_test.items():
        if callable(view_func):
            print(f"✓ {name} é uma função válida")
        else:
            print(f"✗ {name} NÃO é uma função válida")
            
except ImportError as e:
    print(f"✗ Erro ao importar views: {e}")
except Exception as e:
    print(f"✗ Erro inesperado: {e}")

print("\n=== TESTE DE URLS ===")
try:
    from financas.urls import urlpatterns
    print(f"✓ URLs importadas: {len(urlpatterns)} padrões encontrados")
    
    for i, pattern in enumerate(urlpatterns):
        print(f"{i+1}. {pattern.pattern} -> {pattern.callback.__name__ if hasattr(pattern.callback, '__name__') else pattern.callback}")
        
except ImportError as e:
    print(f"✗ Erro ao importar URLs: {e}")
except Exception as e:
    print(f"✗ Erro inesperado nas URLs: {e}")