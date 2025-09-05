#!/usr/bin/env python
import os
from pathlib import Path
from decouple import config

# Verificar se o arquivo .env existe
env_file = Path('.env')
print(f"Arquivo .env existe: {env_file.exists()}")
print(f"Caminho completo: {env_file.absolute()}")

if env_file.exists():
    print("\nConteúdo do .env:")
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)

print("\n=== TESTE DE VARIÁVEIS DE AMBIENTE ===")

# Testar com decouple (como o Django usa)
print("\nUsando python-decouple:")
email_user = config('EMAIL_HOST_USER', default='')
email_password = config('EMAIL_HOST_PASSWORD', default='')

print(f"EMAIL_HOST_USER: '{email_user}'")
print(f"EMAIL_HOST_PASSWORD: '{email_password}'")

# Testar com os.getenv
print("\nUsando os.getenv:")
email_user_os = os.getenv('EMAIL_HOST_USER', '')
email_password_os = os.getenv('EMAIL_HOST_PASSWORD', '')

print(f"EMAIL_HOST_USER: '{email_user_os}'")
print(f"EMAIL_HOST_PASSWORD: '{email_password_os}'")

# Testar carregamento manual do .env
if env_file.exists():
    print("\nCarregando .env manualmente:")
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                if 'EMAIL' in key:
                    print(f"{key}: '{value}'")

    # Testar novamente após carregamento manual
    print("\nApós carregamento manual:")
    print(f"EMAIL_HOST_USER: '{os.getenv('EMAIL_HOST_USER', '')}'")
    print(f"EMAIL_HOST_PASSWORD: '{os.getenv('EMAIL_HOST_PASSWORD', '')}'")