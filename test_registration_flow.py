#!/usr/bin/env python
import os
import sys
import django
from django.test import TestCase, Client
from django.test.utils import setup_test_environment, teardown_test_environment
from django.core import mail
from django.contrib.auth import get_user_model
from django.conf import settings
import re

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

# Setup test environment
setup_test_environment()

User = get_user_model()

def test_registration_flow():
    """Test the complete registration flow with email verification"""
    print("=== Testando Fluxo Completo de Registro ===")
    
    # Clear any existing test users
    test_email = "teste@exemplo.com"
    User.objects.filter(email=test_email).delete()
    
    client = Client()
    
    # Test 1: Registration form submission
    print("\n1. Testando submissão do formulário de registro...")
    
    registration_data = {
        'username': 'usuario_teste_novo',
        'email': test_email,
        'password1': 'senha_teste_123',
        'password2': 'senha_teste_123',
        'tipo_pessoa': 'fisica',
        'cpf': '98765432100'
    }
    
    response = client.post('/registro/', registration_data)
    print(f"Status da resposta: {response.status_code}")
    
    if response.status_code == 302:
        print(f"Redirecionamento para: {response.url}")
    else:
        print(f"Conteúdo da resposta: {response.content.decode()[:500]}...")
    
    # Check if user was created but not active
    try:
        user = User.objects.get(email=test_email)
        print(f"Usuário criado: {user.username}")
        print(f"Usuário ativo: {user.is_active}")
        print(f"Código de verificação gerado: {bool(user.codigo_verificacao)}")
        
        if user.codigo_verificacao:
            print(f"Código: {user.codigo_verificacao}")
            print(f"Código expira em: {user.codigo_verificacao_expira}")
    except User.DoesNotExist:
        print("❌ Usuário não foi criado")
        return False
    
    # Test 2: Check if email was sent
    print("\n2. Verificando envio de email...")
    print(f"Emails na caixa de saída: {len(mail.outbox)}")
    
    if mail.outbox:
        email = mail.outbox[-1]  # Get the last email
        print(f"Para: {email.to}")
        print(f"Assunto: {email.subject}")
        print(f"Corpo do email: {email.body[:200]}...")
        
        # Extract verification code from email
        code_match = re.search(r'código de verificação é: (\d{6})', email.body)
        if code_match:
            verification_code = code_match.group(1)
            print(f"Código extraído do email: {verification_code}")
        else:
            print("❌ Código de verificação não encontrado no email")
            return False
    else:
        print("❌ Nenhum email foi enviado")
        return False
    
    # Test 3: Verification code submission
    print("\n3. Testando submissão do código de verificação...")
    
    verification_response = client.post('/verificar-codigo/', {
        'codigo': verification_code
    })
    
    print(f"Status da verificação: {verification_response.status_code}")
    
    if verification_response.status_code == 302:
        print(f"Redirecionamento após verificação: {verification_response.url}")
    
    # Check if user is now active
    user.refresh_from_db()
    print(f"Usuário ativo após verificação: {user.is_active}")
    
    if user.is_active:
        print("✅ Fluxo de registro completado com sucesso!")
        return True
    else:
        print("❌ Usuário não foi ativado após verificação")
        return False

def test_login_after_verification():
    """Test login after successful verification"""
    print("\n=== Testando Login Após Verificação ===")
    
    client = Client()
    
    login_response = client.post('/login/', {
        'username': 'teste@exemplo.com',
        'password': 'senha_teste_123'
    })
    
    print(f"Status do login: {login_response.status_code}")
    
    if login_response.status_code == 302:
        print(f"Redirecionamento após login: {login_response.url}")
        print("✅ Login realizado com sucesso!")
        return True
    else:
        print("❌ Falha no login")
        return False

if __name__ == '__main__':
    try:
        # Configure email backend for testing
        original_email_backend = settings.EMAIL_BACKEND
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        
        # Clear mail outbox
        mail.outbox.clear()
        
        success = test_registration_flow()
        
        if success:
            test_login_after_verification()
        
        print("\n=== Resumo do Teste ===")
        if success:
            print("✅ Todos os testes passaram!")
            print("✅ Sistema de registro com verificação por email está funcionando")
        else:
            print("❌ Alguns testes falharam")
            
        # Restore original email backend
        settings.EMAIL_BACKEND = original_email_backend
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
    finally:
        teardown_test_environment()