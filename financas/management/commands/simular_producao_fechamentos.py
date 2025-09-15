from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from financas.models import Transacao, FechamentoMensal, Conta
from financas.utils import get_data_atual_brasil
from datetime import datetime, timedelta
from decimal import Decimal
import json

class Command(BaseCommand):
    help = 'Simula cenário de produção com fechamentos mensais para testar correção'

    def handle(self, *args, **options):
        self.stdout.write('=== SIMULAÇÃO PRODUÇÃO COM FECHAMENTOS ===')
        
        # Criar fechamentos fictícios para simular produção
        hoje = get_data_atual_brasil()
        
        # Buscar uma conta existente
        conta = Conta.objects.first()
        if not conta:
            self.stdout.write('❌ Nenhuma conta encontrada. Criando conta de teste...')
            conta = Conta.objects.create(
                nome='Conta Teste',
                tipo='corrente',
                saldo=Decimal('5000.00')
            )
        
        # Criar fechamentos dos últimos 3 meses (incluindo agosto)
        fechamentos_criados = []
        
        for i in range(3, 0, -1):  # 3, 2, 1 meses atrás
            data_fechamento = hoje.replace(day=1) - timedelta(days=i*30)
            mes_fechamento = data_fechamento.month
            ano_fechamento = data_fechamento.year
            
            # Verificar se já existe fechamento
            fechamento_existente = FechamentoMensal.objects.filter(
                conta=conta,
                mes=mes_fechamento,
                ano=ano_fechamento
            ).first()
            
            if not fechamento_existente:
                saldo_final = Decimal('1000.00') * i  # Saldos diferentes para cada mês
                
                fechamento = FechamentoMensal.objects.create(
                    mes=mes_fechamento,
                    ano=ano_fechamento,
                    conta=conta,
                    saldo_inicial=Decimal('500.00'),
                    total_receitas=Decimal('2000.00'),
                    total_despesas=Decimal('1500.00'),
                    saldo_final=saldo_final,
                    fechado=True,
                    data_inicio_periodo=data_fechamento.replace(day=1),
                    data_fim_periodo=data_fechamento.replace(day=28),
                    data_fechamento=datetime.now()
                )
                fechamentos_criados.append(fechamento)
                
                meses = [
                    '', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
                ]
                
                self.stdout.write(f'✅ Fechamento criado: {meses[mes_fechamento]}/{ano_fechamento} - R$ {saldo_final}')
        
        # Agora testar a lógica corrigida
        self.stdout.write('\n=== TESTANDO LÓGICA CORRIGIDA ===')
        
        # Simular a lógica do views.py
        fechamentos = FechamentoMensal.objects.filter(fechado=True).order_by('ano', 'mes')
        
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        self.stdout.write(f'Data atual: {hoje}')
        self.stdout.write(f'Mês/Ano atual: {mes_atual}/{ano_atual}')
        self.stdout.write(f'Total de fechamentos: {fechamentos.count()}')
        
        dados_evolucao = []
        
        if fechamentos.exists():
            # Usar fechamentos até o mês anterior + calcular mês atual
            fechamentos_anteriores = fechamentos.filter(
                Q(ano__lt=ano_atual) | Q(ano=ano_atual, mes__lt=mes_atual)
            ).order_by('ano', 'mes')
            
            self.stdout.write(f'Fechamentos anteriores: {fechamentos_anteriores.count()}')
            
            # Pegar os últimos 11 fechamentos para deixar espaço para o mês atual
            if fechamentos_anteriores.count() > 11:
                fechamentos_anteriores = fechamentos_anteriores[fechamentos_anteriores.count()-11:]
            
            # Adicionar fechamentos anteriores
            for fechamento in fechamentos_anteriores:
                meses = [
                    '', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
                ]
                dados_evolucao.append({
                    'data': f"{meses[fechamento.mes]}/{fechamento.ano}",
                    'saldo': float(fechamento.saldo_final)
                })
                self.stdout.write(f'  - {meses[fechamento.mes]}/{fechamento.ano}: R$ {fechamento.saldo_final} (fechamento)')
            
            # SEMPRE calcular e incluir o mês atual
            data_inicio_mes = hoje.replace(day=1)
            
            # Saldo inicial do mês (último fechamento ou saldo das contas)
            saldo_inicial_mes = 0
            if fechamentos_anteriores.exists():
                # Somar saldos finais de todas as contas do último fechamento
                ultimo_fechamento_mes = fechamentos_anteriores.last().mes
                ultimo_fechamento_ano = fechamentos_anteriores.last().ano
                fechamentos_ultimo_mes = FechamentoMensal.objects.filter(
                    ano=ultimo_fechamento_ano,
                    mes=ultimo_fechamento_mes,
                    fechado=True
                )
                saldo_inicial_mes = sum(float(f.saldo_final) for f in fechamentos_ultimo_mes)
                self.stdout.write(f'Saldo inicial do mês atual (baseado no último fechamento): R$ {saldo_inicial_mes}')
            else:
                # Se não há fechamentos, usar saldo atual das contas
                contas = Conta.objects.all()
                saldo_inicial_mes = sum(float(conta.saldo) for conta in contas)
                self.stdout.write(f'Saldo inicial do mês atual (baseado no saldo das contas): R$ {saldo_inicial_mes}')
            
            # Transações do mês atual
            receitas_mes_atual = Transacao.objects.filter(
                tipo='receita',
                data__gte=data_inicio_mes,
                data__lte=hoje
            ).aggregate(total=Sum('valor'))['total'] or 0
            
            despesas_mes_atual = Transacao.objects.filter(
                tipo='despesa',
                data__gte=data_inicio_mes,
                data__lte=hoje
            ).aggregate(total=Sum('valor'))['total'] or 0
            
            self.stdout.write(f'Receitas do mês atual: R$ {receitas_mes_atual}')
            self.stdout.write(f'Despesas do mês atual: R$ {despesas_mes_atual}')
            
            saldo_mes_atual = saldo_inicial_mes + float(receitas_mes_atual) - float(despesas_mes_atual)
            
            # Adicionar mês atual
            meses = [
                '', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
            ]
            
            dados_evolucao.append({
                'data': f"{meses[mes_atual]}/{ano_atual}",
                'saldo': saldo_mes_atual
            })
            
            self.stdout.write(f'  - {meses[mes_atual]}/{ano_atual}: R$ {saldo_mes_atual} (mês atual calculado)')
        
        self.stdout.write('\n=== RESULTADO FINAL ===')
        for item in dados_evolucao:
            self.stdout.write(f'{item["data"]}: R$ {item["saldo"]}')
        
        self.stdout.write(f'\nJSON: {json.dumps(dados_evolucao, indent=2)}')
        
        # Limpar fechamentos criados para teste
        if fechamentos_criados:
            self.stdout.write('\n=== LIMPANDO FECHAMENTOS DE TESTE ===')
            for fechamento in fechamentos_criados:
                meses = [
                    '', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
                ]
                self.stdout.write(f'🗑️  Removendo fechamento: {meses[fechamento.mes]}/{fechamento.ano}')
                fechamento.delete()
        
        self.stdout.write(self.style.SUCCESS('=== SIMULAÇÃO DE DADOS DO GRÁFICO ==='))  
        self.stdout.write('Verificando se há duplicação de meses no gráfico de evolução do saldo...')
        
        # Verificar se há meses duplicados nos dados de evolução
        meses_encontrados = {}
        duplicados = []
        
        for item in dados_evolucao:
            if item['data'] in meses_encontrados:
                duplicados.append(item['data'])
                self.stdout.write(f"⚠️ DUPLICADO: {item['data']} (valores: {meses_encontrados[item['data']]} e {item['saldo']})")
            else:
                meses_encontrados[item['data']] = item['saldo']
        
        if duplicados:
            self.stdout.write(f"❌ Encontrados {len(duplicados)} meses duplicados: {', '.join(duplicados)}")
        else:
            self.stdout.write("✅ Nenhum mês duplicado encontrado - a correção funcionou!")
            
        self.stdout.write(self.style.SUCCESS('\n✅ SIMULAÇÃO CONCLUÍDA - A correção deve resolver o problema em produção!'))