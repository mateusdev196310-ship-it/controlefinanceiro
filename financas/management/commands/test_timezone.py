from django.core.management.base import BaseCommand
from financas.utils import get_data_atual_brasil
from datetime import datetime
import pytz

class Command(BaseCommand):
    help = 'Testa a função de timezone para verificar se está funcionando corretamente'
    
    def handle(self, *args, **options):
        self.stdout.write("=== TESTE DE TIMEZONE ===")
        
        # Teste da função get_data_atual_brasil
        try:
            data_brasil = get_data_atual_brasil()
            self.stdout.write(f"✓ get_data_atual_brasil(): {data_brasil}")
            self.stdout.write(f"  Tipo: {type(data_brasil)}")
        except Exception as e:
            self.stdout.write(f"✗ Erro em get_data_atual_brasil(): {e}")
        
        # Comparação com datetime.now().date()
        try:
            data_utc = datetime.now().date()
            self.stdout.write(f"✓ datetime.now().date(): {data_utc}")
            self.stdout.write(f"  Tipo: {type(data_utc)}")
        except Exception as e:
            self.stdout.write(f"✗ Erro em datetime.now().date(): {e}")
        
        # Teste do timezone do Brasil
        try:
            tz_brasil = pytz.timezone('America/Sao_Paulo')
            agora_brasil = datetime.now(tz_brasil)
            self.stdout.write(f"✓ Agora no Brasil: {agora_brasil}")
            self.stdout.write(f"  Data: {agora_brasil.date()}")
            self.stdout.write(f"  Hora: {agora_brasil.time()}")
        except Exception as e:
            self.stdout.write(f"✗ Erro no timezone do Brasil: {e}")
        
        # Comparação das datas
        try:
            data_brasil = get_data_atual_brasil()
            data_utc = datetime.now().date()
            diferenca = (data_brasil - data_utc).days
            self.stdout.write(f"\n=== COMPARAÇÃO ===")
            self.stdout.write(f"Data Brasil: {data_brasil}")
            self.stdout.write(f"Data UTC: {data_utc}")
            self.stdout.write(f"Diferença em dias: {diferenca}")
            
            if diferenca == 0:
                self.stdout.write("✓ As datas são iguais")
            else:
                self.stdout.write(f"⚠ As datas diferem por {diferenca} dia(s)")
                
        except Exception as e:
            self.stdout.write(f"✗ Erro na comparação: {e}")
        
        self.stdout.write("\n=== FIM DO TESTE ===")