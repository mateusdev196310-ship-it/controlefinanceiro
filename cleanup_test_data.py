#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def cleanup_test_users():
    """Remove any existing test users"""
    print("=== Limpando dados de teste ===")
    
    # Remove users with test email
    test_emails = ['teste@exemplo.com', 'usuario_teste@exemplo.com']
    
    for email in test_emails:
        users = User.objects.filter(email=email)
        if users.exists():
            print(f"Removendo {users.count()} usuário(s) com email {email}")
            users.delete()
    
    # Remove users with test username
    test_usernames = ['usuario_teste', 'teste_usuario']
    
    for username in test_usernames:
        users = User.objects.filter(username=username)
        if users.exists():
            print(f"Removendo {users.count()} usuário(s) com username {username}")
            users.delete()
    
    # Remove users with test CPF
    test_cpf = '12345678901'
    users = User.objects.filter(cpf=test_cpf)
    if users.exists():
        print(f"Removendo {users.count()} usuário(s) com CPF {test_cpf}")
        users.delete()
    
    # Remove users with test schema_name
    test_schema = f'user_{test_cpf}'
    users = User.objects.filter(schema_name=test_schema)
    if users.exists():
        print(f"Removendo {users.count()} usuário(s) com schema_name {test_schema}")
        users.delete()
    
    print("✅ Limpeza concluída!")

if __name__ == '__main__':
    cleanup_test_users()