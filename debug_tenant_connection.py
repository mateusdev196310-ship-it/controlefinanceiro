import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection
from financas.models import DespesaParcelada, Categoria, Conta, Transacao
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== DEBUG TENANT CONNECTION ===")

# Verificar se tenant_id está na conexão
print(f"connection.tenant_id: {getattr(connection, 'tenant_id', 'NÃO DEFINIDO')}")

# Verificar usuário atual
user = User.objects.get(username='mateus')
print(f"Usuário: {user.username} (ID: {user.id})")

# Definir tenant_id manualmente
connection.tenant_id = user.id
print(f"Tenant ID definido manualmente: {connection.tenant_id}")

# Testar criação com tenant_id definido
print("\n=== TESTANDO CRIAÇÃO COM TENANT_ID DEFINIDO ===")

try:
    categoria = Categoria.objects.first()
    conta = Conta.objects.first()
    
    print(f"Categoria: {categoria.nome} (Tenant: {categoria.tenant_id})")
    print(f"Conta: {conta.nome} (Tenant: {conta.tenant_id})")
    
    # Criar despesa usando o manager
    despesa = DespesaParcelada.objects.create(
        descricao="Teste com Tenant ID",
        valor_total=1000.00,
        numero_parcelas=5,
        data_primeira_parcela='2024-02-01',
        categoria=categoria,
        conta=conta,
        responsavel=user.username
    )
    
    print(f"\n✅ Despesa criada:")
    print(f"   ID: {despesa.id}")
    print(f"   Descrição: {despesa.descricao}")
    print(f"   Tenant ID: {despesa.tenant_id}")
    
    # Gerar parcelas
    despesa.gerar_parcelas()
    
    # Verificar parcelas
    parcelas = Transacao.objects.filter(despesa_parcelada=despesa)
    print(f"\n   Parcelas geradas: {parcelas.count()}")
    
    for parcela in parcelas[:3]:
        print(f"   - Parcela {parcela.numero_parcela}: Tenant ID {parcela.tenant_id}")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n=== DEBUG CONCLUÍDO ===")