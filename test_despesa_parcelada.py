#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import *
from django.contrib.auth.models import User
from datetime import date, timedelta

try:
    # Obter usuário admin
    user = User.objects.get(username='admin')
    print(f"Usuário encontrado: {user.username}")
    
    # Verificar categorias e contas
    categorias = list(Categoria.objects.all())
    contas = list(Conta.objects.all())
    
    print(f"Categorias disponíveis: {len(categorias)}")
    print(f"Contas disponíveis: {len(contas)}")
    
    # Criar conta se não existir
    if not contas:
        print('Criando conta de teste...')
        conta = Conta.objects.create(
            nome='Conta Corrente',
            saldo_inicial=1000.00,
            tipo='corrente'
        )
        contas = [conta]
        print(f"Conta criada: {conta.nome}")
    
    # Criar despesa parcelada se tiver categorias e contas
    if categorias and contas:
        despesa = DespesaParcelada.objects.create(
            descricao='Teste Pagamento Parcela',
            valor_total=300.00,
            categoria=categorias[0],
            responsavel=user.username,
            numero_parcelas=3,
            data_primeira_parcela=date.today(),
            dia_vencimento=15,
            intervalo_tipo='mensal',
            conta=contas[0]
        )
        
        # Gerar parcelas
        despesa.gerar_parcelas()
        print(f"Despesa parcelada criada: ID {despesa.id}")
        
        # Listar parcelas criadas
        transacoes = Transacao.objects.filter(despesa_parcelada=despesa)
        print(f"Parcelas criadas: {transacoes.count()}")
        
        for t in transacoes:
            print(f"Parcela {t.numero_parcela}: ID {t.id}, Valor R$ {t.valor}")
    else:
        print("Não foi possível criar despesa parcelada - faltam categorias ou contas")
        
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()