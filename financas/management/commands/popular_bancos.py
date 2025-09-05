from django.core.management.base import BaseCommand
from financas.models import Banco

class Command(BaseCommand):
    help = 'Popula a tabela de bancos com os principais bancos brasileiros'
    
    def handle(self, *args, **options):
        bancos_data = [
            {'codigo': '001', 'nome': 'Banco do Brasil', 'imagem': 'financas/images/banco-do-brasil.svg'},
            {'codigo': '104', 'nome': 'Caixa Econômica Federal', 'imagem': 'financas/images/caixa.svg'},
            {'codigo': '237', 'nome': 'Bradesco', 'imagem': 'financas/images/bradesco.svg'},
            {'codigo': '341', 'nome': 'Itaú Unibanco', 'imagem': 'financas/images/itau.svg'},
            {'codigo': '033', 'nome': 'Santander', 'imagem': ''},
            {'codigo': '260', 'nome': 'Nu Pagamentos (Nubank)', 'imagem': 'financas/images/nubank.svg'},
            {'codigo': '077', 'nome': 'Banco Inter', 'imagem': ''},
            {'codigo': '212', 'nome': 'Banco Original', 'imagem': ''},
            {'codigo': '290', 'nome': 'PagSeguro', 'imagem': ''},
            {'codigo': '323', 'nome': 'Mercado Pago', 'imagem': ''},
        ]
        
        for banco_data in bancos_data:
            banco, created = Banco.objects.get_or_create(
                codigo=banco_data['codigo'],
                defaults={
                    'nome': banco_data['nome'],
                    'imagem': banco_data['imagem']
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Banco {banco.nome} criado com sucesso!')
                )
            else:
                # Atualizar a imagem mesmo se o banco já existir
                banco.imagem = banco_data['imagem']
                banco.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Banco {banco.nome} atualizado com nova imagem.')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Comando executado com sucesso!')
        )