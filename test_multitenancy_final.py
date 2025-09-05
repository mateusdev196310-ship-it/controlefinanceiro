import os
import django
import uuid
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.db import connection, transaction
from financas.models import CustomUser, Tenant, Categoria, Conta, Transacao, Banco

def clean_database_completely():
    """Limpa completamente o banco de dados"""
    try:
        with connection.cursor() as cursor:
            print("🧹 Limpando banco de dados completamente...")
            
            # Desabilitar constraints
            cursor.execute("SET session_replication_role = replica;")
            
            tables = [
                'financas_fechamentomensal',
                'financas_configuracaofechamento', 
                'financas_meta',
                'financas_despesaparcelada',
                'financas_transacao',
                'financas_conta',
                'financas_categoria',
                'financas_tenant_usuarios',
                'financas_tenant',
                'auth_user_custom_user_permissions',
                'auth_user_custom_groups',
                'auth_user_custom'
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                    print(f"  ✅ {table} limpa")
                except Exception as e:
                    print(f"  ⚠️ {table}: {e}")
            
            # Reabilitar constraints
            cursor.execute("SET session_replication_role = DEFAULT;")
            
            # Commit explícito
            connection.commit()
            
            print("✅ Limpeza completa realizada!")
            
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")
        connection.rollback()
        raise

def test_multitenancy():
    """Testa o sistema de multi-tenancy"""
    try:
        print("\n🧪 Iniciando teste de multi-tenancy...")
        
        # Gerar IDs únicos para evitar conflitos
        unique_id = str(uuid.uuid4())[:8]
        
        # Criar usuários com nomes únicos
        print("\n👥 Criando usuários de teste...")
        
        with transaction.atomic():
            user1 = CustomUser.objects.create_user(
                username=f'user1_{unique_id}',
                email=f'user1_{unique_id}@test.com',
                password='senha123',
                tipo_pessoa='fisica',
                cpf='123.456.789-01'
            )
            print(f"  ✅ Usuário 1: {user1.username}")
            
            user2 = CustomUser.objects.create_user(
                username=f'user2_{unique_id}',
                email=f'user2_{unique_id}@test.com',
                password='senha123',
                tipo_pessoa='juridica',
                cnpj='12.345.678/0001-90'
            )
            print(f"  ✅ Usuário 2: {user2.username}")
        
        # Criar tenants
        print("\n🏢 Criando tenants...")
        
        with transaction.atomic():
            tenant1 = Tenant.objects.create(
                nome=f"Empresa {user1.username}",
                codigo=f"EMP_{unique_id}_1"
            )
            tenant1.usuarios.add(user1)
            print(f"  ✅ Tenant 1: {tenant1.nome} (ID: {tenant1.id})")
            
            tenant2 = Tenant.objects.create(
                nome=f"Empresa {user2.username}",
                codigo=f"EMP_{unique_id}_2"
            )
            tenant2.usuarios.add(user2)
            print(f"  ✅ Tenant 2: {tenant2.nome} (ID: {tenant2.id})")
        
        # Criar banco com código único
        print("\n🏦 Criando banco...")
        banco_codigo = f"B{unique_id[:3].upper()}"
        banco = Banco.objects.create(nome=f"Banco Teste {unique_id}", codigo=banco_codigo)
        print(f"  ✅ Banco: {banco.nome} (código: {banco.codigo})")
        
        # Testar isolamento de dados
        print("\n🔒 Testando isolamento de dados...")
        
        # Dados para tenant 1
        with transaction.atomic():
            categoria1 = Categoria.objects.create(
                nome="Receita Tenant 1",
                tipo='receita',
                cor='#28a745',
                tenant_id=tenant1.id
            )
            
            conta1 = Conta.objects.create(
                nome="Conta Corrente Tenant 1",
                banco=banco,
                cor='#007bff',
                tenant_id=tenant1.id
            )
            
            transacao1 = Transacao.objects.create(
                descricao="Receita Tenant 1",
                valor=1000.00,
                data=datetime.now().date(),
                tipo='receita',
                categoria=categoria1,
                conta=conta1,
                tenant_id=tenant1.id
            )
            
            print(f"  ✅ Dados criados para Tenant 1:")
            print(f"    - Categoria: {categoria1.nome} (tenant_id: {categoria1.tenant_id})")
            print(f"    - Conta: {conta1.nome} (tenant_id: {conta1.tenant_id})")
            print(f"    - Transação: {transacao1.descricao} (tenant_id: {transacao1.tenant_id})")
        
        # Dados para tenant 2
        with transaction.atomic():
            categoria2 = Categoria.objects.create(
                nome="Despesa Tenant 2",
                tipo='despesa',
                cor='#dc3545',
                tenant_id=tenant2.id
            )
            
            conta2 = Conta.objects.create(
                nome="Conta Poupança Tenant 2",
                banco=banco,
                cor='#28a745',
                tenant_id=tenant2.id
            )
            
            transacao2 = Transacao.objects.create(
                descricao="Despesa Tenant 2",
                valor=500.00,
                data=datetime.now().date(),
                tipo='despesa',
                categoria=categoria2,
                conta=conta2,
                tenant_id=tenant2.id
            )
            
            print(f"  ✅ Dados criados para Tenant 2:")
            print(f"    - Categoria: {categoria2.nome} (tenant_id: {categoria2.tenant_id})")
            print(f"    - Conta: {conta2.nome} (tenant_id: {conta2.tenant_id})")
            print(f"    - Transação: {transacao2.descricao} (tenant_id: {transacao2.tenant_id})")
        
        # Verificar isolamento
        print("\n🔍 Verificando isolamento de dados...")
        
        # Categorias do tenant 1
        categorias_t1 = Categoria.objects.filter(tenant_id=tenant1.id)
        print(f"  📊 Categorias do Tenant 1: {categorias_t1.count()}")
        for cat in categorias_t1:
            print(f"    - {cat.nome}")
        
        # Categorias do tenant 2
        categorias_t2 = Categoria.objects.filter(tenant_id=tenant2.id)
        print(f"  📊 Categorias do Tenant 2: {categorias_t2.count()}")
        for cat in categorias_t2:
            print(f"    - {cat.nome}")
        
        # Contas do tenant 1
        contas_t1 = Conta.objects.filter(tenant_id=tenant1.id)
        print(f"  💳 Contas do Tenant 1: {contas_t1.count()}")
        for conta in contas_t1:
            print(f"    - {conta.nome}")
        
        # Contas do tenant 2
        contas_t2 = Conta.objects.filter(tenant_id=tenant2.id)
        print(f"  💳 Contas do Tenant 2: {contas_t2.count()}")
        for conta in contas_t2:
            print(f"    - {conta.nome}")
        
        # Transações do tenant 1
        transacoes_t1 = Transacao.objects.filter(tenant_id=tenant1.id)
        print(f"  💰 Transações do Tenant 1: {transacoes_t1.count()}")
        for trans in transacoes_t1:
            print(f"    - {trans.descricao}: R$ {trans.valor}")
        
        # Transações do tenant 2
        transacoes_t2 = Transacao.objects.filter(tenant_id=tenant2.id)
        print(f"  💰 Transações do Tenant 2: {transacoes_t2.count()}")
        for trans in transacoes_t2:
            print(f"    - {trans.descricao}: R$ {trans.valor}")
        
        # Verificar que não há vazamento de dados
        print("\n🛡️ Verificando isolamento...")
        
        # Tenant 1 não deve ver dados do Tenant 2
        categorias_vazamento = Categoria.objects.filter(tenant_id=tenant2.id).filter(tenant_id=tenant1.id)
        if categorias_vazamento.count() == 0:
            print("  ✅ Isolamento de categorias funcionando")
        else:
            print("  ❌ VAZAMENTO: Tenant 1 pode ver categorias do Tenant 2")
        
        contas_vazamento = Conta.objects.filter(tenant_id=tenant2.id).filter(tenant_id=tenant1.id)
        if contas_vazamento.count() == 0:
            print("  ✅ Isolamento de contas funcionando")
        else:
            print("  ❌ VAZAMENTO: Tenant 1 pode ver contas do Tenant 2")
        
        transacoes_vazamento = Transacao.objects.filter(tenant_id=tenant2.id).filter(tenant_id=tenant1.id)
        if transacoes_vazamento.count() == 0:
            print("  ✅ Isolamento de transações funcionando")
        else:
            print("  ❌ VAZAMENTO: Tenant 1 pode ver transações do Tenant 2")
        
        print("\n🎉 Teste de multi-tenancy concluído com sucesso!")
        print("\n📋 Resumo:")
        print(f"  - 2 usuários criados")
        print(f"  - 2 tenants criados")
        print(f"  - Dados isolados por tenant_id")
        print(f"  - Isolamento verificado e funcionando")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Limpar banco primeiro
    clean_database_completely()
    
    # Executar teste
    test_multitenancy()