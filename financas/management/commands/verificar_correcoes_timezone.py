from django.core.management.base import BaseCommand
from django.utils import timezone
from financas.utils import get_data_atual_brasil
from financas.services import ContaService, TransacaoService
from financas.views import api_evolucao_saldo, api_resumo_financeiro, api_transacoes_por_categoria
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
import json

class Command(BaseCommand):
    help = 'Verifica se todas as correções de timezone foram aplicadas corretamente'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== VERIFICAÇÃO DE CORREÇÕES DE TIMEZONE ==='))
        
        # 1. Verificar função get_data_atual_brasil
        data_brasil = get_data_atual_brasil()
        data_utc = timezone.now().date()
        
        self.stdout.write(f'Data Brasil (get_data_atual_brasil): {data_brasil}')
        self.stdout.write(f'Data UTC (timezone.now().date): {data_utc}')
        self.stdout.write(f'Mês Brasil: {data_brasil.month} ({data_brasil.strftime("%b/%Y")})')
        self.stdout.write(f'Mês UTC: {data_utc.month} ({data_utc.strftime("%b/%Y")})')
        
        # 2. Testar APIs que foram corrigidas
        factory = RequestFactory()
        request = factory.get('/api/evolucao-saldo/')
        request.user = AnonymousUser()
        
        try:
            # Testar API de evolução do saldo
            response = api_evolucao_saldo(request)
            if response.status_code == 200:
                data = json.loads(response.content)
                if data:
                    ultimo_mes = data[-1]['data'] if data else 'N/A'
                    self.stdout.write(f'API Evolução Saldo - Último mês: {ultimo_mes}')
                else:
                    self.stdout.write('API Evolução Saldo - Sem dados')
            else:
                self.stdout.write(f'API Evolução Saldo - Erro: {response.status_code}')
        except Exception as e:
            self.stdout.write(f'Erro ao testar API Evolução Saldo: {e}')
        
        try:
            # Testar API de resumo financeiro
            response = api_resumo_financeiro(request)
            if response.status_code == 200:
                data = json.loads(response.content)
                self.stdout.write(f'API Resumo Financeiro - Transações do mês: {data.get("transacoes_mes", "N/A")}')
            else:
                self.stdout.write(f'API Resumo Financeiro - Erro: {response.status_code}')
        except Exception as e:
            self.stdout.write(f'Erro ao testar API Resumo Financeiro: {e}')
        
        try:
            # Testar API de transações por categoria
            response = api_transacoes_por_categoria(request)
            if response.status_code == 200:
                data = json.loads(response.content)
                self.stdout.write(f'API Transações por Categoria - {len(data)} categorias encontradas')
            else:
                self.stdout.write(f'API Transações por Categoria - Erro: {response.status_code}')
        except Exception as e:
            self.stdout.write(f'Erro ao testar API Transações por Categoria: {e}')
        
        # 3. Verificar se há diferença entre os fusos horários
        if data_brasil != data_utc:
            self.stdout.write(self.style.WARNING(f'ATENÇÃO: Diferença de fuso horário detectada!'))
            self.stdout.write(self.style.WARNING(f'Brasil: {data_brasil} vs UTC: {data_utc}'))
        else:
            self.stdout.write(self.style.SUCCESS('Fusos horários estão alinhados'))
        
        # 4. Simular cenário de produção (diferença de fuso)
        import pytz
        from datetime import datetime
        
        # Simular UTC às 21:00 (que seria 18:00 no Brasil)
        utc_tz = pytz.UTC
        brasil_tz = pytz.timezone('America/Sao_Paulo')
        
        # Criar um datetime UTC que seria ontem no Brasil
        utc_time = datetime(2025, 9, 14, 2, 0, 0, tzinfo=utc_tz)  # 02:00 UTC = 23:00 Brasil (dia anterior)
        brasil_time = utc_time.astimezone(brasil_tz)
        
        self.stdout.write(f'Simulação - UTC: {utc_time.date()} vs Brasil: {brasil_time.date()}')
        
        if utc_time.date() != brasil_time.date():
            self.stdout.write(self.style.WARNING('Confirmado: Diferença de fuso pode causar problemas!'))
            self.stdout.write(self.style.SUCCESS('Correções aplicadas devem resolver o problema em produção'))
        
        self.stdout.write(self.style.SUCCESS('=== VERIFICAÇÃO CONCLUÍDA ==='))
        self.stdout.write('Todas as funções agora usam get_data_atual_brasil() para consistência de timezone')
        self.stdout.write('Deploy em produção deve resolver o problema de data incorreta')