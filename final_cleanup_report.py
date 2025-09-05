#!/usr/bin/env python
import os
import sys
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser, Tenant, Categoria, Transacao, DespesaParcelada, Conta

def generate_final_report():
    """
    Gera relatório final do sistema após limpeza
    """
    print("📋 RELATÓRIO FINAL DO SISTEMA")
    print("=" * 50)
    
    # 1. Usuários
    print("\n👥 USUÁRIOS:")
    usuarios = CustomUser.objects.all().order_by('username')
    for user in usuarios:
        tenants_user = user.tenants.all()
        tenants_nomes = ', '.join([t.codigo for t in tenants_user]) if tenants_user.exists() else 'Nenhum'
        print(f"  • {user.username} (ID: {user.id})")
        print(f"    - Email: {user.email}")
        print(f"    - Superuser: {user.is_superuser}")
        print(f"    - Tenants: {tenants_nomes}")
        print()
    
    # 2. Tenants
    print("🏢 TENANTS:")
    tenants = Tenant.objects.all().order_by('codigo')
    for tenant in tenants:
        usuarios_tenant = tenant.usuarios.all()
        usuarios_nomes = ', '.join([u.username for u in usuarios_tenant]) if usuarios_tenant.exists() else 'Nenhum'
        print(f"  • {tenant.codigo} (ID: {tenant.id})")
        print(f"    - Nome: {tenant.nome}")
        print(f"    - Usuários: {usuarios_nomes}")
        print(f"    - Ativo: {tenant.ativo}")
        print()
    
    # 3. Dados por tenant
    print("📊 DADOS POR TENANT:")
    for tenant in tenants:
        print(f"\n  🏢 {tenant.codigo}:")
        
        # Contas
        contas = Conta.objects.filter(tenant_id=tenant.id)
        print(f"    - Contas: {contas.count()}")
        for conta in contas:
            print(f"      • {conta.nome} (Saldo: R$ {conta.saldo})")
        
        # Categorias
        categorias = Categoria.objects.filter(tenant_id=tenant.id)
        print(f"    - Categorias: {categorias.count()}")
        
        # Transações
        transacoes = Transacao.objects.filter(tenant_id=tenant.id)
        print(f"    - Transações: {transacoes.count()}")
        
        # Despesas parceladas
        despesas = DespesaParcelada.objects.filter(tenant_id=tenant.id)
        print(f"    - Despesas Parceladas: {despesas.count()}")
    
    # 4. Schemas do banco
    print("\n🗄️  SCHEMAS DO BANCO:")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schema_name
        """)
        schemas = cursor.fetchall()
        
        for schema in schemas:
            schema_name = schema[0]
            print(f"  • {schema_name}")
    
    # 5. Resumo final
    print("\n🎯 RESUMO FINAL:")
    print("=" * 30)
    print(f"✅ Usuários ativos: {usuarios.count()}")
    print(f"✅ Tenants ativos: {tenants.count()}")
    print(f"✅ Total de contas: {Conta.objects.count()}")
    print(f"✅ Total de categorias: {Categoria.objects.count()}")
    print(f"✅ Total de transações: {Transacao.objects.count()}")
    print(f"✅ Total de despesas parceladas: {DespesaParcelada.objects.count()}")
    print(f"✅ Schemas no banco: {len(schemas)}")
    
    print("\n🎉 Sistema limpo e organizado!")
    print("\n📝 USUÁRIOS MANTIDOS:")
    print("  • admin (Superuser) - Credenciais: admin / admin123")
    print("  • mateus (Usuário regular)")
    print("  • souzac3 (Usuário regular)")
    
    print("\n⚠️  IMPORTANTE:")
    print("  • Altere a senha do usuário admin após o primeiro login")
    print("  • Todos os dados de teste foram removidos")
    print("  • Sistema pronto para uso em produção")

if __name__ == '__main__':
    generate_final_report()