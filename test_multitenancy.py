import os
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Categoria, Conta, Transacao, Banco, CustomUser
from decimal import Decimal
from datetime import date

def test_multitenancy():
    print("=== Teste de Multi-Tenancy ===")
    
    # Criar dois usuários de teste
    print("\n1. Criando usuários de teste...")
    
    # Limpar usuários de teste existentes
    CustomUser.objects.filter(username__in=['tenant1', 'tenant2']).delete()
    
    user1 = CustomUser.objects.create_user(
        username='tenant1',
        email='tenant1@test.com',
        password='test123',
        tipo_pessoa='fisica',
        cpf='12345678901'
    )
    
    user2 = CustomUser.objects.create_user(
        username='tenant2', 
        email='tenant2@test.com',
        password='test123',
        tipo_pessoa='fisica',
        cpf='98765432109'
    )
    
    print(f"Usuário 1 criado: {user1.username} (ID: {user1.id})")
    print(f"Usuário 2 criado: {user2.username} (ID: {user2.id})")
    
    # Criar banco para testes
    banco_teste = Banco.objects.get_or_create(
        codigo='001',
        defaults={'nome': 'Banco Teste'}
    )[0]
    
    # Teste 1: Criar dados para o tenant 1
    print("\n2. Criando dados para Tenant 1...")
    connection.tenant_id = user1.id
    
    categoria1 = Categoria.objects.create(
        nome='Alimentação Tenant 1',
        cor='#FF0000',
        tipo='despesa'
    )
    
    conta1 = Conta.objects.create(
        nome='Conta Corrente Tenant 1',
        saldo=Decimal('1000.00'),
        tipo='corrente',
        banco=banco_teste
    )
    
    transacao1 = Transacao.objects.create(
        data=date.today(),
        descricao='Compra supermercado Tenant 1',
        valor=Decimal('150.00'),
        tipo='despesa',
        categoria=categoria1,
        conta=conta1
    )
    
    print(f"Categoria criada: {categoria1.nome} (tenant_id: {categoria1.tenant_id})")
    print(f"Conta criada: {conta1.nome} (tenant_id: {conta1.tenant_id})")
    print(f"Transação criada: {transacao1.descricao} (tenant_id: {transacao1.tenant_id})")
    
    # Teste 2: Criar dados para o tenant 2
    print("\n3. Criando dados para Tenant 2...")
    connection.tenant_id = user2.id
    
    categoria2 = Categoria.objects.create(
        nome='Transporte Tenant 2',
        cor='#00FF00',
        tipo='despesa'
    )
    
    conta2 = Conta.objects.create(
        nome='Conta Poupança Tenant 2',
        saldo=Decimal('2000.00'),
        tipo='poupanca',
        banco=banco_teste
    )
    
    transacao2 = Transacao.objects.create(
        data=date.today(),
        descricao='Combustível Tenant 2',
        valor=Decimal('80.00'),
        tipo='despesa',
        categoria=categoria2,
        conta=conta2
    )
    
    print(f"Categoria criada: {categoria2.nome} (tenant_id: {categoria2.tenant_id})")
    print(f"Conta criada: {conta2.nome} (tenant_id: {conta2.tenant_id})")
    print(f"Transação criada: {transacao2.descricao} (tenant_id: {transacao2.tenant_id})")
    
    # Teste 3: Verificar isolamento - Tenant 1 deve ver apenas seus dados
    print("\n4. Testando isolamento de dados...")
    connection.tenant_id = user1.id
    
    categorias_tenant1 = Categoria.objects.all()
    contas_tenant1 = Conta.objects.all()
    transacoes_tenant1 = Transacao.objects.all()
    
    print(f"\nTenant 1 vê:")
    print(f"  - {categorias_tenant1.count()} categoria(s): {[c.nome for c in categorias_tenant1]}")
    print(f"  - {contas_tenant1.count()} conta(s): {[c.nome for c in contas_tenant1]}")
    print(f"  - {transacoes_tenant1.count()} transação(ões): {[t.descricao for t in transacoes_tenant1]}")
    
    # Teste 4: Verificar isolamento - Tenant 2 deve ver apenas seus dados
    connection.tenant_id = user2.id
    
    categorias_tenant2 = Categoria.objects.all()
    contas_tenant2 = Conta.objects.all()
    transacoes_tenant2 = Transacao.objects.all()
    
    print(f"\nTenant 2 vê:")
    print(f"  - {categorias_tenant2.count()} categoria(s): {[c.nome for c in categorias_tenant2]}")
    print(f"  - {contas_tenant2.count()} conta(s): {[c.nome for c in contas_tenant2]}")
    print(f"  - {transacoes_tenant2.count()} transação(ões): {[t.descricao for t in transacoes_tenant2]}")
    
    # Teste 5: Verificar dados sem filtro de tenant (acesso direto ao banco)
    print("\n5. Verificando dados totais no banco (sem filtro de tenant)...")
    connection.tenant_id = None
    
    # Usar queryset sem o manager customizado
    total_categorias = Categoria.objects.using('default').extra(where=["1=1"]).count()
    total_contas = Conta.objects.using('default').extra(where=["1=1"]).count()
    total_transacoes = Transacao.objects.using('default').extra(where=["1=1"]).count()
    
    print(f"Total no banco (sem filtro):")
    print(f"  - {total_categorias} categoria(s)")
    print(f"  - {total_contas} conta(s)")
    print(f"  - {total_transacoes} transação(ões)")
    
    # Verificar resultados
    print("\n6. Resultados do teste:")
    success = True
    
    if categorias_tenant1.count() != 1 or contas_tenant1.count() != 1 or transacoes_tenant1.count() != 1:
        print("❌ FALHA: Tenant 1 não vê exatamente seus dados")
        success = False
    else:
        print("✅ SUCESSO: Tenant 1 vê apenas seus dados")
    
    if categorias_tenant2.count() != 1 or contas_tenant2.count() != 1 or transacoes_tenant2.count() != 1:
        print("❌ FALHA: Tenant 2 não vê exatamente seus dados")
        success = False
    else:
        print("✅ SUCESSO: Tenant 2 vê apenas seus dados")
    
    if total_categorias < 2 or total_contas < 2 or total_transacoes < 2:
        print("❌ FALHA: Dados não foram criados corretamente no banco")
        success = False
    else:
        print("✅ SUCESSO: Todos os dados estão no banco")
    
    if success:
        print("\n🎉 MULTI-TENANCY FUNCIONANDO CORRETAMENTE!")
    else:
        print("\n❌ PROBLEMAS DETECTADOS NO MULTI-TENANCY")
    
    # Limpeza
    print("\n7. Limpando dados de teste...")
    connection.tenant_id = None
    CustomUser.objects.filter(username__in=['tenant1', 'tenant2']).delete()
    print("Dados de teste removidos.")

if __name__ == '__main__':
    test_multitenancy()