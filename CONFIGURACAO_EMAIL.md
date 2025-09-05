# Configuração de Email para Verificação

## Problema Corrigido

✅ **Erro de timezone corrigido**: O erro "can't compare offset-naive and offset-aware datetimes" foi resolvido substituindo `datetime.now()` por `timezone.now()` do Django.

## Configuração de Email

Para que os emails sejam enviados para o endereço cadastrado (ao invés de aparecer apenas no terminal), siga os passos:

### 1. Configurar Gmail (Recomendado)

1. **Ativar verificação em 2 etapas** na sua conta Google
2. **Gerar senha de app**:
   - Acesse: https://myaccount.google.com/apppasswords
   - Selecione "Mail" e "Windows Computer"
   - Copie a senha gerada (16 caracteres)

### 2. Atualizar arquivo .env

Edite o arquivo `.env` na raiz do projeto:

```env
# Configurações de Email
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app_de_16_caracteres
```

**⚠️ IMPORTANTE**: Use a senha de app, não sua senha normal do Gmail!

### 3. Alternativa para Desenvolvimento

Se preferir continuar vendo os emails no terminal durante desenvolvimento, edite `financeiro/settings.py`:

```python
# Descomente esta linha para emails no console:
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Comente estas linhas:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
```

## Como Testar

1. Reinicie o servidor Django
2. Acesse: http://127.0.0.1:8000/registro/
3. Cadastre-se com um email válido
4. Verifique:
   - **Com SMTP**: Email chegará na caixa de entrada
   - **Com console**: Código aparecerá no terminal

## Outros Provedores de Email

### Outlook/Hotmail
```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
```

### Yahoo
```python
EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 587
```

## Solução de Problemas

- **Email não chega**: Verifique spam/lixo eletrônico
- **Erro de autenticação**: Confirme se está usando senha de app
- **Timeout**: Verifique conexão com internet
- **Ainda aparece no terminal**: Reinicie o servidor após alterar settings.py