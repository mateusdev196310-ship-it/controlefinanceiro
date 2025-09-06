#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.test import Client
from financas.models import Categoria, Conta
from django.contrib.auth.models import User
from financas.models import CustomUser

def test_criar_transacao():
    try:
        # Criar cliente de teste
        client = Client()
        
        # Fazer login
        login_success = client.login(username='admin', password='admin123')
        print(f"Login success: {login_success}")
        
        if not login_success:
            print("Falha no login")
            return
        
        # Obter categoria e conta
        categoria = Categoria.objects.first()
        conta = Conta.objects.first()
        
        print(f"Categoria: {categoria}")
        print(f"Conta: {conta}")
        
        if not categoria or not conta:
            print("Categoria ou conta não encontrada")
            return
        
        # Obter página de criação
        response = client.get('/transacoes/criar/')
        print(f"GET Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Erro ao acessar página: {response.content.decode()[:500]}")
            return
        
        # Extrair CSRF token do HTML
        content = response.content.decode()
        import re
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', content)
        if csrf_match:
            csrf_token = csrf_match.group(1)
        else:
            print("CSRF token não encontrado")
            return
        
        print(f"CSRF token: {csrf_token[:20]}...")
        
        # Dados da transação
        data = {
            'descricao': 'Transação de Teste',
            'valor': '50.00',
            'tipo': 'despesa',
            'categoria': categoria.id,
            'conta': conta.id,
            'data': '2025-01-05',
            'csrfmiddlewaretoken': csrf_token
        }
        
        print(f"Dados: {data}")
        
        # Fazer POST
        response = client.post('/transacoes/criar/', data)
        print(f"POST Status: {response.status_code}")
        
        if response.status_code != 200 and response.status_code != 302:
            print(f"Erro na criação: {response.content.decode()[:1000]}")
        else:
            print("Transação criada com sucesso!")
            
    except Exception as e:
        print(f"Exceção: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_criar_transacao()