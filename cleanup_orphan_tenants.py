#!/usr/bin/env python
import os
import sys
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser, Tenant
from django.contrib.auth.hashers import make_password

def cleanup_orphan_tenants():
    """
    Remove tenants órfãos (sem usuários) e cria usuário admin se necessário
    """
    print("🧹 Limpando tenants órfãos...")
    
    try:
        # 1. Identificar tenants órfãos
        tenants_orfaos = Tenant.objects.filter(usuarios__isnull=True)
        
        print(f"\n🎯 Tenants órfãos encontrados: {tenants_orfaos.count()}")
        
        if tenants_orfaos.count() > 0:
            for tenant in tenants_orfaos:
                print(f"  - ID: {tenant.id}, Código: '{tenant.codigo}'")
            
            # Confirmar remoção
            confirmacao = input("\n⚠️  Confirma a remoção destes tenants órfãos? (digite 'SIM' para confirmar): ")
            if confirmacao == 'SIM':
                # Remover dados relacionados aos tenants órfãos
                with connection.cursor() as cursor:
                    for tenant in tenants_orfaos:
                        print(f"  🗑️  Removendo dados do tenant órfão {tenant.codigo} (ID: {tenant.id})")
                        
                        # Remover dados das tabelas que possuem tenant_id
                        cursor.execute("DELETE FROM financas_transacao WHERE tenant_id = %s", [tenant.id])
                        cursor.execute("DELETE FROM financas_despesaparcelada WHERE tenant_id = %s", [tenant.id])
                        cursor.execute("DELETE FROM financas_conta WHERE tenant_id = %s", [tenant.id])
                        cursor.execute("DELETE FROM financas_categoria WHERE tenant_id = %s", [tenant.id])
                        
                        # Nota: FechamentoMensal e ConfiguracaoFechamento não possuem tenant_id
                        # Eles são relacionados através da Conta, que já foi removida acima
                
                # Remover os tenants órfãos
                tenants_removidos = tenants_orfaos.count()
                tenants_orfaos.delete()
                print(f"  ✅ {tenants_removidos} tenants órfãos removidos com sucesso")
            else:
                print("❌ Remoção de tenants cancelada.")
        else:
            print("✅ Nenhum tenant órfão encontrado.")
        
        # 2. Verificar se existe usuário admin
        print("\n👤 Verificando usuário admin...")
        
        try:
            admin_user = CustomUser.objects.get(username='admin')
            print(f"✅ Usuário admin já existe (ID: {admin_user.id})")
        except CustomUser.DoesNotExist:
            print("⚠️  Usuário admin não encontrado.")
            criar_admin = input("Deseja criar o usuário admin? (digite 'SIM' para confirmar): ")
            
            if criar_admin == 'SIM':
                # Criar usuário admin
                admin_user = CustomUser.objects.create(
                    username='admin',
                    email='admin@sistema.com',
                    first_name='Administrador',
                    last_name='Sistema',
                    is_staff=True,
                    is_superuser=True,
                    is_active=True,
                    password=make_password('admin123'),  # Senha padrão
                    tipo_pessoa='fisica',
                    cpf='00000000000'
                )
                
                print(f"✅ Usuário admin criado com sucesso (ID: {admin_user.id})")
                print("📝 Credenciais: admin / admin123")
                print("⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
        
        # 3. Relatório final
        print("\n📊 RELATÓRIO FINAL:")
        print("=" * 40)
        
        # Usuários restantes
        usuarios = CustomUser.objects.all().order_by('username')
        print(f"👥 Usuários no sistema: {usuarios.count()}")
        for user in usuarios:
            print(f"  - {user.username} (Superuser: {user.is_superuser})")
        
        # Tenants restantes
        tenants = Tenant.objects.all().order_by('codigo')
        print(f"\n🏢 Tenants no sistema: {tenants.count()}")
        for tenant in tenants:
            usuarios_tenant = tenant.usuarios.all()
            usuarios_nomes = ', '.join([u.username for u in usuarios_tenant]) if usuarios_tenant.exists() else 'Nenhum'
            print(f"  - {tenant.codigo} (Usuários: {usuarios_nomes})")
        
        print("\n🎉 Limpeza concluída!")
        
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    cleanup_orphan_tenants()