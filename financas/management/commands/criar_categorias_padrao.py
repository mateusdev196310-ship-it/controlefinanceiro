from django.core.management.base import BaseCommand
from financas.models import Categoria

class Command(BaseCommand):
    help = 'Cria categorias padrão no sistema'
    
    def handle(self, *args, **options):
        categorias_padrao = [
            # Receitas
            {'nome': 'Salário', 'cor': '#28a745', 'tipo': 'receita'},
            {'nome': 'Freelance', 'cor': '#17a2b8', 'tipo': 'receita'},
            {'nome': 'Investimentos', 'cor': '#ffc107', 'tipo': 'receita'},
            
            # Despesas Essenciais
            {'nome': 'Alimentação', 'cor': '#fd7e14', 'tipo': 'despesa'},
            {'nome': 'Transporte', 'cor': '#6f42c1', 'tipo': 'despesa'},
            {'nome': 'Moradia', 'cor': '#e83e8c', 'tipo': 'despesa'},
            {'nome': 'Saúde', 'cor': '#dc3545', 'tipo': 'despesa'},
            {'nome': 'Educação', 'cor': '#20c997', 'tipo': 'despesa'},
            
            # Despesas Variáveis
            {'nome': 'Lazer', 'cor': '#6610f2', 'tipo': 'despesa'},
            {'nome': 'Compras', 'cor': '#fd7e14', 'tipo': 'despesa'},
            {'nome': 'Serviços', 'cor': '#6c757d', 'tipo': 'despesa'},
        ]
        
        criadas = 0
        existentes = 0
        
        for categoria_data in categorias_padrao:
            categoria, created = Categoria.objects.get_or_create(
                nome=categoria_data['nome'],
                defaults={
                    'cor': categoria_data['cor'],
                    'tipo': categoria_data['tipo']
                }
            )
            
            if created:
                criadas += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Categoria "{categoria.nome}" criada')
                )
            else:
                existentes += 1
                self.stdout.write(
                    self.style.WARNING(f'⚠ Categoria "{categoria.nome}" já existe')
                )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Processo concluído: {criadas} criadas, {existentes} já existiam'
            )
        )