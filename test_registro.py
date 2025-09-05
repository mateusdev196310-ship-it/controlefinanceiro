#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser
from financas.views import enviar_codigo_verificacao
from django.utils import timezone
import secrets
import string

def gerar_codigo_verificacao():
    """Gera um código de verificação de 6 dígitos"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def test_registro_email():
    email = 'mateus9811sc3@gmail.com'
    
    # Remover usuário existente se houver
    CustomUser.objects.filter(email=email).delete()
    
    # Criar novo usuário
    codigo = gerar_codigo_verificacao()
    expiracao = timezone.now() + timezone.timedelta(hours=24)
    
    user = CustomUser.objects.create_user(
        username='testuser',
        email=email,
        password='testpass123',
        tipo_pessoa='fisica',
        codigo_verificacao=codigo,
        codigo_verificacao_expira=expiracao,
        is_active=False
    )
    
    print(f"Usuário criado: {user.username}")
    print(f"Email: {user.email}")
    print(f"Código de verificação: {user.codigo_verificacao}")
    print(f"Expiração: {user.codigo_verificacao_expira}")
    
    # Tentar enviar email
    try:
        resultado = enviar_codigo_verificacao(user.email, user.codigo_verificacao)
        print(f"Resultado do envio: {resultado}")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
    
    return user

if __name__ == '__main__':
    print("=== TESTE DE REGISTRO E ENVIO DE EMAIL ===")
    user = test_registro_email()
    print("\n=== TESTE CONCLUÍDO ===")
    print(f"\nPara validar o código, use: {user.codigo_verificacao}")