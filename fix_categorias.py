import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Categoria, Transacao, DespesaParcelada, FechamentoMensal, ConfiguracaoFechamento
from django.db import transaction

print('=== LIMPANDO DADOS E RECRIANDO CATEGORIAS ===')

# Limpar todos os dados
with transaction.atomic():
    print('Removendo transações...')
    Transacao.objects.all().delete()
    
    print('Removendo despesas parceladas...')
    DespesaParcelada.objects.all().delete()
    
    print('Removendo fechamentos mensais...')
    FechamentoMensal.objects.all().delete()
    
    print('Removendo configurações de fechamento...')
    ConfiguracaoFechamento.objects.all().delete()
    
    print('Removendo categorias antigas...')
    Categoria.objects.all().delete()
    
    print('Criando novas categorias com cores corretas...')
    
    # Categorias com cores corretas
    categorias_novas = [
        {'nome': 'Alimentação', 'cor': '#fd7e14', 'tipo': 'despesa'},
        {'nome': 'Transporte', 'cor': '#6f42c1', 'tipo': 'despesa'},
        {'nome': 'Moradia', 'cor': '#e83e8c', 'tipo': 'despesa'},
        {'nome': 'Saúde', 'cor': '#dc3545', 'tipo': 'despesa'},
        {'nome': 'Educação', 'cor': '#20c997', 'tipo': 'despesa'},
        {'nome': 'Lazer', 'cor': '#6610f2', 'tipo': 'despesa'},
        {'nome': 'Compras', 'cor': '#e510d3', 'tipo': 'despesa'},
        {'nome': 'Serviços', 'cor': '#17a2b8', 'tipo': 'despesa'},
        {'nome': 'Salário', 'cor': '#28a745', 'tipo': 'receita'},
        {'nome': 'Freelance', 'cor': '#ffc107', 'tipo': 'receita'},
        {'nome': 'Investimentos', 'cor': '#007bff', 'tipo': 'receita'},
        {'nome': 'Outros', 'cor': '#6c757d', 'tipo': 'ambos'},
    ]
    
    for cat_data in categorias_novas:
        categoria = Categoria.objects.create(
            nome=cat_data['nome'],
            cor=cat_data['cor'],
            tipo=cat_data['tipo']
        )
        print(f'Criada: {categoria.nome} - {categoria.cor} ({categoria.tipo})')
    
    print(f'\nTotal de categorias criadas: {Categoria.objects.count()}')
    
print('\n=== VERIFICANDO CATEGORIAS CRIADAS ===')
for cat in Categoria.objects.all().order_by('nome'):
    print(f'✓ {cat.nome} - Cor: {cat.cor} - Tipo: {cat.tipo}')

print('\n✅ Dados limpos e categorias recriadas com sucesso!')
print('🎨 Todas as cores estão agora no campo correto!')
print('📊 Sistema pronto para uso com dados zerados!')