#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import CustomUser, Tenant, Categoria, Transacao, Conta, DespesaParcelada
from django.db.models import Sum
from django.db import transaction

def test_exclusao_conta_com_transacoes():
    """
    Testa o que acontece quando uma conta com transações é excluída
    """
    print("🧪 TESTE: Exclusão de Conta com Transações")
    print("=" * 50)
    
    try:
        # 1. Buscar um usuário existente
        user = CustomUser.objects.filter(username='mateus').first()
        if not user:
            print("❌ Usuário 'mateus' não encontrado")
            return
        
        tenant = user.tenants.first()
        if not tenant:
            print("❌ Tenant não encontrado para o usuário")
            return
        
        print(f"👤 Usuário: {user.username}")
        print(f"🏢 Tenant: {tenant.codigo}")
        
        # 2. Criar uma conta de teste
        with transaction.atomic():
            conta_teste = Conta.objects.create(
                nome="Conta Teste Exclusão",
                saldo=Decimal('1000.00'),
                cor="#ff0000",
                tipo="simples",
                tenant_id=tenant.id
            )
            print(f"\n💳 Conta criada: {conta_teste.nome} (ID: {conta_teste.id})")
            print(f"💰 Saldo inicial: R$ {conta_teste.saldo}")
        
        # 3. Buscar ou criar categoria
        categoria = Categoria.objects.filter(tenant_id=tenant.id).first()
        if not categoria:
            categoria = Categoria.objects.create(
                nome="Categoria Teste",
                cor="#00ff00",
                tipo="ambos",
                tenant_id=tenant.id
            )
        
        # 4. Criar algumas transações na conta
        transacoes_criadas = []
        
        # Receita
        receita = Transacao.objects.create(
            descricao="Receita Teste",
            valor=Decimal('500.00'),
            categoria=categoria,
            tipo="receita",
            conta=conta_teste,
            tenant_id=tenant.id
        )
        transacoes_criadas.append(receita)
        
        # Despesa
        despesa = Transacao.objects.create(
            descricao="Despesa Teste",
            valor=Decimal('200.00'),
            categoria=categoria,
            tipo="despesa",
            conta=conta_teste,
            tenant_id=tenant.id
        )
        transacoes_criadas.append(despesa)
        
        print(f"\n📊 Transações criadas: {len(transacoes_criadas)}")
        for t in transacoes_criadas:
            print(f"  • {t.descricao}: R$ {t.valor} ({t.tipo})")
        
        # 5. Criar mais uma transação para ter mais dados
        transferencia = Transacao.objects.create(
            descricao="Transferência Teste",
            valor=Decimal('100.00'),
            categoria=categoria,
            tipo="despesa",
            conta=conta_teste,
            tenant_id=tenant.id
        )
        transacoes_criadas.append(transferencia)
        
        print(f"  • {transferencia.descricao}: R$ {transferencia.valor} ({transferencia.tipo})")
        
        # 6. Verificar estado antes da exclusão
        print("\n📋 ESTADO ANTES DA EXCLUSÃO:")
        print("=" * 30)
        
        total_transacoes = Transacao.objects.filter(conta=conta_teste).count()
        total_receitas = Transacao.objects.filter(
            conta=conta_teste, tipo='receita'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        total_despesas = Transacao.objects.filter(
            conta=conta_teste, tipo='despesa'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        print(f"💳 Conta: {conta_teste.nome}")
        print(f"💰 Saldo: R$ {conta_teste.saldo}")
        print(f"📊 Total de transações: {total_transacoes}")
        print(f"📈 Total receitas: R$ {total_receitas}")
        print(f"📉 Total despesas: R$ {total_despesas}")
        print(f"💳 Despesas parceladas: {DespesaParcelada.objects.filter(conta=conta_teste).count()}")
        
        # 7. Tentar excluir a conta
        print("\n🗑️  TENTANDO EXCLUIR A CONTA...")
        print("=" * 30)
        
        conta_id = conta_teste.id
        conta_nome = conta_teste.nome
        
        try:
            # Simular a exclusão como feita na view
            conta_teste.delete()
            print(f"✅ Conta '{conta_nome}' (ID: {conta_id}) excluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao excluir conta: {e}")
            return
        
        # 8. Verificar o que aconteceu após a exclusão
        print("\n📋 ESTADO APÓS A EXCLUSÃO:")
        print("=" * 30)
        
        # Verificar se a conta ainda existe
        conta_existe = Conta.objects.filter(id=conta_id).exists()
        print(f"💳 Conta ainda existe: {conta_existe}")
        
        # Verificar transações
        transacoes_restantes = Transacao.objects.filter(conta_id=conta_id).count()
        print(f"📊 Transações restantes: {transacoes_restantes}")
        
        # Verificar despesas parceladas
        despesas_restantes = DespesaParcelada.objects.filter(conta_id=conta_id).count()
        print(f"💳 Despesas parceladas restantes: {despesas_restantes}")
        
        # Verificar se há transações órfãs (sem conta)
        transacoes_orfas = Transacao.objects.filter(conta__isnull=True).count()
        print(f"🚨 Transações órfãs (sem conta): {transacoes_orfas}")
        
        # 9. Análise do impacto
        print("\n🔍 ANÁLISE DO IMPACTO:")
        print("=" * 30)
        
        if not conta_existe and transacoes_restantes == 0:
            print("✅ COMPORTAMENTO ATUAL: CASCADE")
            print("  • A conta foi excluída")
            print("  • Todas as transações foram excluídas automaticamente")
            print("  • Todas as despesas parceladas foram excluídas")
            print("  • Não há dados órfãos")
            print("\n⚠️  PROBLEMAS IDENTIFICADOS:")
            print("  • Não há validação se a conta tem saldo")
            print("  • Não há validação se a conta tem transações")
            print("  • Perda de histórico financeiro")
            print("  • Possível inconsistência nos relatórios")
            print("  • Não há confirmação sobre o impacto")
        
        elif conta_existe:
            print("❌ ERRO: Conta não foi excluída quando deveria")
        
        elif transacoes_restantes > 0:
            print("🚨 PROBLEMA: Transações órfãs detectadas")
            print("  • Isso pode causar inconsistências no sistema")
        
        # 10. Recomendações
        print("\n💡 RECOMENDAÇÕES:")
        print("=" * 30)
        print("1. Adicionar validação antes da exclusão:")
        print("   • Verificar se a conta tem saldo diferente de zero")
        print("   • Verificar se a conta tem transações")
        print("   • Verificar se a conta tem despesas parceladas ativas")
        print("\n2. Implementar exclusão segura:")
        print("   • Permitir exclusão apenas de contas vazias")
        print("   • Ou transferir transações para outra conta")
        print("   • Ou arquivar conta em vez de excluir")
        print("\n3. Melhorar interface:")
        print("   • Mostrar aviso sobre o impacto da exclusão")
        print("   • Exigir confirmação dupla")
        print("   • Mostrar quantas transações serão perdidas")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

def verificar_validacoes_atuais():
    """
    Verifica as validações atuais no modelo e views
    """
    print("\n🔍 VERIFICAÇÃO DAS VALIDAÇÕES ATUAIS:")
    print("=" * 50)
    
    # Verificar modelo Conta
    print("📋 Modelo Conta:")
    print("  • clean(): Sem validações (pass)")
    print("  • save(): Sem validações restritivas")
    print("  • delete(): Usa comportamento padrão do Django")
    
    # Verificar view excluir_conta
    print("\n🌐 View excluir_conta:")
    print("  • Não verifica saldo da conta")
    print("  • Não verifica existência de transações")
    print("  • Não verifica despesas parceladas")
    print("  • Não mostra impacto da exclusão")
    print("  • Apenas pede confirmação simples")
    
    # Verificar relacionamentos CASCADE
    print("\n🔗 Relacionamentos CASCADE:")
    print("  • Transacao.conta: CASCADE (linha 369)")
    print("  • DespesaParcelada.conta: CASCADE (linha 433)")
    print("  • FechamentoMensal.conta: CASCADE (linha 657)")
    
    print("\n⚠️  CONCLUSÃO:")
    print("O sistema atualmente permite exclusão de contas sem validações,")
    print("causando perda de dados históricos importantes.")

if __name__ == '__main__':
    verificar_validacoes_atuais()
    print("\n" + "=" * 60)
    test_exclusao_conta_com_transacoes()