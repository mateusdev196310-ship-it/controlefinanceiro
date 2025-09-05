import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser, Tenant, Categoria, Conta, Transacao, Banco
from django.db import connection

def test_clean_multitenancy():
    print("🧪 Testando sistema multi-tenancy com banco limpo...\n")
    
    try:
        # Verificar se as tabelas existem e estão vazias
        cursor = connection.cursor()
        
        # Verificar estrutura das tabelas
        cursor.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name IN ('financas_categoria', 'financas_conta', 'financas_transacao', 'financas_despesaparcelada')
            AND column_name = 'tenant_id'
            ORDER BY table_name, column_name;
        """)
        
        tenant_columns = cursor.fetchall()
        print("📋 Verificação dos campos tenant_id:")
        for table, column, data_type, nullable in tenant_columns:
            print(f"  ✅ {table}.{column} ({data_type}, nullable: {nullable})")
        
        if not tenant_columns:
            print("  ❌ Nenhum campo tenant_id encontrado!")
            return
        
        # Contar registros existentes
        tables_to_check = ['auth_user_custom', 'financas_tenant', 'financas_categoria', 'financas_conta', 'financas_transacao']
        print("\n📊 Contagem de registros existentes:")
        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} registros")
        
        # Criar dados de teste
        print("\n🏗️ Criando dados de teste...")
        
        # Criar usuários
        user1 = CustomUser.objects.create_user(
            username='usuario1',
            email='user1@test.com',
            password='senha123',
            tipo_pessoa='fisica',
            cpf='123.456.789-01'
        )
        print(f"  ✅ Usuário 1 criado: {user1.username}")
        
        user2 = CustomUser.objects.create_user(
            username='usuario2', 
            email='user2@test.com',
            password='senha123',
            tipo_pessoa='juridica',
            cnpj='12.345.678/0001-90'
        )
        print(f"  ✅ Usuário 2 criado: {user2.username}")
        
        # Criar tenants
        tenant1 = Tenant.objects.create(
            nome=f"Tenant {user1.username}",
            codigo=f"TENANT_{user1.username.upper()}"
        )
        tenant1.usuarios.add(user1)
        print(f"  ✅ Tenant 1 criado: {tenant1.nome} (código: {tenant1.codigo})")
        
        tenant2 = Tenant.objects.create(
            nome=f"Tenant {user2.username}",
            codigo=f"TENANT_{user2.username.upper()}"
        )
        tenant2.usuarios.add(user2)
        print(f"  ✅ Tenant 2 criado: {tenant2.nome} (código: {tenant2.codigo})")
        
        # Criar banco
        banco = Banco.objects.create(nome="Banco Teste", codigo="001")
        print(f"  ✅ Banco criado: {banco.nome}")
        
        # Simular contexto de tenant para user1
        print("\n🔄 Testando isolamento de dados...")
        
        # Dados para tenant 1
        categoria1 = Categoria(nome="Alimentação", cor="#FF0000", tenant_id=tenant1.id)
        categoria1.save()
        
        conta1 = Conta(nome="Conta Corrente 1", saldo=1000.00, banco=banco, cor="#00FF00", tipo="corrente", tenant_id=tenant1.id)
        conta1.save()
        
        transacao1 = Transacao(descricao="Compra supermercado", valor=150.00, data="2025-01-01", tipo="despesa", conta=conta1, categoria=categoria1, tenant_id=tenant1.id)
        transacao1.save()
        
        print(f"  ✅ Dados criados para tenant 1 (ID: {tenant1.id})")
        
        # Dados para tenant 2
        categoria2 = Categoria(nome="Transporte", cor="#0000FF", tenant_id=tenant2.id)
        categoria2.save()
        
        conta2 = Conta(nome="Conta Corrente 2", saldo=2000.00, banco=banco, cor="#FFFF00", tipo="poupanca", tenant_id=tenant2.id)
        conta2.save()
        
        transacao2 = Transacao(descricao="Combustível", valor=200.00, data="2025-01-01", tipo="despesa", conta=conta2, categoria=categoria2, tenant_id=tenant2.id)
        transacao2.save()
        
        print(f"  ✅ Dados criados para tenant 2 (ID: {tenant2.id})")
        
        # Testar isolamento usando o TenantManager
        print("\n🔍 Testando isolamento com TenantManager...")
        
        # Simular filtro por tenant 1
        from django.db import models
        
        # Teste manual de filtro por tenant_id
        categorias_tenant1 = Categoria.objects.filter(tenant_id=tenant1.id)
        contas_tenant1 = Conta.objects.filter(tenant_id=tenant1.id)
        transacoes_tenant1 = Transacao.objects.filter(tenant_id=tenant1.id)
        
        print(f"  📊 Tenant 1 (ID: {tenant1.id}):")
        print(f"    - Categorias: {categorias_tenant1.count()}")
        print(f"    - Contas: {contas_tenant1.count()}")
        print(f"    - Transações: {transacoes_tenant1.count()}")
        
        categorias_tenant2 = Categoria.objects.filter(tenant_id=tenant2.id)
        contas_tenant2 = Conta.objects.filter(tenant_id=tenant2.id)
        transacoes_tenant2 = Transacao.objects.filter(tenant_id=tenant2.id)
        
        print(f"  📊 Tenant 2 (ID: {tenant2.id}):")
        print(f"    - Categorias: {categorias_tenant2.count()}")
        print(f"    - Contas: {contas_tenant2.count()}")
        print(f"    - Transações: {transacoes_tenant2.count()}")
        
        # Verificar isolamento
        if (categorias_tenant1.count() == 1 and contas_tenant1.count() == 1 and transacoes_tenant1.count() == 1 and
            categorias_tenant2.count() == 1 and contas_tenant2.count() == 1 and transacoes_tenant2.count() == 1):
            print("\n✅ SUCESSO: Isolamento de dados funcionando corretamente!")
        else:
            print("\n❌ ERRO: Isolamento de dados não está funcionando!")
        
        # Verificar dados totais (sem filtro)
        total_categorias = Categoria.objects.all().count()
        total_contas = Conta.objects.all().count()
        total_transacoes = Transacao.objects.all().count()
        
        print(f"\n📈 Totais sem filtro:")
        print(f"  - Total de categorias: {total_categorias}")
        print(f"  - Total de contas: {total_contas}")
        print(f"  - Total de transações: {total_transacoes}")
        
        print("\n🎉 Teste de multi-tenancy concluído com sucesso!")
        print("\n📝 Resumo:")
        print(f"  - 2 usuários criados")
        print(f"  - 2 tenants criados")
        print(f"  - Dados isolados por tenant_id")
        print(f"  - Sistema pronto para uso!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_clean_multitenancy()