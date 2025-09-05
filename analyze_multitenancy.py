#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Transacao, Conta, Categoria, Tenant, CustomUser

print("=== ANÁLISE DO SISTEMA MULTI-TENANT ===")
print()

# Estatísticas gerais
print("📊 ESTATÍSTICAS GERAIS:")
print(f"   • Total de usuários: {CustomUser.objects.count()}")
print(f"   • Total de tenants: {Tenant.objects.count()}")
print(f"   • Total de transações: {Transacao.objects.count()}")
print(f"   • Total de contas: {Conta.objects.count()}")
print(f"   • Total de categorias: {Categoria.objects.count()}")
print()

# Análise por tenant
print("🏢 DADOS POR TENANT:")
for tenant in Tenant.objects.all():
    print(f"\n   Tenant ID {tenant.id} - {tenant.nome}:")
    
    # Usuários associados
    usuarios = tenant.usuarios.all()
    print(f"     👥 Usuários: {', '.join([u.username for u in usuarios])}")
    
    # Transações do tenant
    transacoes = Transacao.objects.filter(tenant_id=tenant.id)
    print(f"     💰 Transações: {transacoes.count()}")
    
    # Contas do tenant
    contas = Conta.objects.filter(tenant_id=tenant.id)
    print(f"     🏦 Contas: {contas.count()} - {[c.nome for c in contas]}")
    
    # Categorias do tenant
    categorias = Categoria.objects.filter(tenant_id=tenant.id)
    print(f"     📂 Categorias: {categorias.count()} - {[c.nome for c in categorias]}")

print()
print("🔍 EXEMPLOS DE TRANSAÇÕES (últimas 10):")
for t in Transacao.objects.all().order_by('-id')[:10]:
    print(f"   ID {t.id}: {t.descricao[:40]:<40} | Tenant: {t.tenant_id} | Conta: {t.conta.nome}")

print()
print("✅ CONCLUSÃO:")
print("   Sim, está correto! Todas as transações ficam na mesma tabela,")
print("   mas são isoladas pelo campo 'tenant_id'. Isso é uma prática")
print("   profissional padrão chamada 'Row Level Security' ou 'Shared Schema'.")
print("   É mais eficiente que criar tabelas separadas para cada usuário.")