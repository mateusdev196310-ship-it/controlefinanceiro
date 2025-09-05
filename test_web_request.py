#!/usr/bin/env python
import os
import django
from django.test import Client
from django.contrib.auth import get_user_model
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import DespesaParcelada, Categoria, Conta

# Definir tenant_id
connection.tenant_id = 7

print("=== Teste de Requisição Web ===")
print(f"Tenant ID: {connection.tenant_id}")

# Obter categoria e conta válidas
categoria = Categoria.objects.filter(tenant_id=7).first()
conta = Conta.objects.filter(tenant_id=7).first()

if not categoria or not conta:
    print("Erro: Categoria ou conta não encontrada para tenant_id=7")
    exit(1)

print(f"Usando categoria: {categoria.nome} (ID: {categoria.id})")
print(f"Usando conta: {conta.nome} (ID: {conta.id})")
print()

# Criar um usuário de teste se não existir
User = get_user_model()
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={
        'email': 'test@example.com',
        'tipo_pessoa': 'fisica'
    }
)

if created:
    user.set_password('testpass123')
    user.save()
    print(f"Usuário de teste criado: {user.username}")
else:
    print(f"Usando usuário existente: {user.username}")

# Criar cliente de teste
client = Client()

# Fazer login
login_success = client.login(username='testuser', password='testpass123')
print(f"Login realizado: {login_success}")

if not login_success:
    print("Erro: Não foi possível fazer login")
    exit(1)

# Dados do formulário para testar
form_data = {
    'descricao': 'Teste Web Request',
    'valor_total': '600,00',  # Formato que pode vir do JavaScript
    'categoria': str(categoria.id),
    'conta': str(conta.id),
    'responsavel': 'Teste',
    'total_parcelas': '6',
    'data_primeira_parcela': '2024-06-15',
    'intervalo': 'mensal'
}

print("Dados do formulário:")
for key, value in form_data.items():
    print(f"  {key}: '{value}'")
print()

# Fazer requisição POST
response = client.post('/adicionar-despesa-parcelada/', form_data)

print(f"Status da resposta: {response.status_code}")
print(f"URL de redirecionamento: {response.get('Location', 'Nenhum')}")

# Verificar se a despesa foi criada
despesas = DespesaParcelada.objects.filter(descricao='Teste Web Request')
if despesas.exists():
    despesa = despesas.first()
    print(f"\nDespesa criada com sucesso!")
    print(f"  ID: {despesa.id}")
    print(f"  Descrição: {despesa.descricao}")
    print(f"  Valor Total: {despesa.valor_total}")
    print(f"  Valor Parcela: {despesa.valor_parcela}")
    print(f"  Número de Parcelas: {despesa.numero_parcelas}")
    print(f"  Parcelas geradas: {despesa.get_parcelas().count()}")
    print(f"  Tenant ID: {despesa.tenant_id}")
else:
    print("\nNenhuma despesa foi criada!")
    
    # Verificar se há mensagens de erro
    if hasattr(response, 'context') and response.context:
        messages = response.context.get('messages', [])
        if messages:
            print("Mensagens:")
            for message in messages:
                print(f"  - {message}")

print("\n=== Teste concluído ===")