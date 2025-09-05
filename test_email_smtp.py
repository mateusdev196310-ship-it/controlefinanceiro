#!/usr/bin/env python
import os
import django
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.conf import settings
from decouple import config

def test_smtp_direct():
    """Testa SMTP diretamente sem Django"""
    print("=== TESTE SMTP DIRETO ===")
    
    email_user = config('EMAIL_HOST_USER', default='')
    email_password = config('EMAIL_HOST_PASSWORD', default='')
    
    print(f"Email: {email_user}")
    print(f"Password: {'*' * len(email_password) if email_password else 'VAZIO'}")
    
    try:
        # Conectar ao servidor SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        print("Tentando autenticar...")
        server.login(email_user, email_password)
        print("✓ Autenticação bem-sucedida!")
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = 'mateus9811sc3@gmail.com'
        msg['Subject'] = 'Teste SMTP - Sistema Financeiro'
        
        body = """Seu código de verificação é: 144639
        
Este código expira em 24 horas.
        
Se você não solicitou este código, ignore este email."""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Enviar email
        text = msg.as_string()
        server.sendmail(email_user, 'mateus9811sc3@gmail.com', text)
        server.quit()
        
        print("✓ Email enviado com sucesso!")
        return True
        
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

def test_django_email():
    """Testa email via Django"""
    print("\n=== TESTE DJANGO EMAIL ===")
    
    from django.core.mail import send_mail
    
    try:
        result = send_mail(
            'Código de Verificação - Sistema Financeiro',
            'Seu código de verificação é: 144639\n\nEste código expira em 24 horas.',
            settings.EMAIL_HOST_USER,
            ['mateus9811sc3@gmail.com'],
            fail_silently=False
        )
        print(f"✓ Django email enviado! Resultado: {result}")
        return True
    except Exception as e:
        print(f"✗ Erro Django: {e}")
        return False

if __name__ == '__main__':
    print("=== DIAGNÓSTICO DE EMAIL ===")
    
    # Verificar configurações
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    
    # Testar SMTP direto
    smtp_ok = test_smtp_direct()
    
    # Testar Django se SMTP funcionou
    if smtp_ok:
        django_ok = test_django_email()
        if django_ok:
            print("\n🎉 TODOS OS TESTES PASSARAM! O email foi enviado para mateus9811sc3@gmail.com")
        else:
            print("\n⚠️ SMTP funciona, mas Django falhou")
    else:
        print("\n❌ SMTP falhou - verifique as credenciais")