#!/usr/bin/env python
"""
Teste de Stress - Concorrência Intensiva
Teste mais intensivo para verificar os limites do sistema com múltiplos usuários
"""

import os
import sys
import django
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
import statistics

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from django.contrib.auth import get_user_model
from financas.models import Tenant, Categoria, Conta, Transacao, DespesaParcelada
from django.db import transaction, connection
from django.test import Client
from django.urls import reverse
import json

User = get_user_model()

class StressConcurrentTest:
    def __init__(self):
        self.results = []
        self.errors = []
        self.response_times = []
        self.lock = threading.Lock()
        
    def cleanup_test_data(self):
        """Limpa dados de teste anteriores"""
        try:
            # Remover usuários de teste
            test_users = User.objects.filter(username__startswith='stressuser_')
            tenant_ids = []
            
            for user in test_users:
                for tenant in user.tenants.all():
                    tenant_ids.append(tenant.id)
            
            # Remover dados relacionados
            if tenant_ids:
                Transacao.objects.filter(tenant_id__in=tenant_ids).delete()
                DespesaParcelada.objects.filter(tenant_id__in=tenant_ids).delete()
                Categoria.objects.filter(tenant_id__in=tenant_ids).delete()
                Conta.objects.filter(tenant_id__in=tenant_ids).delete()
                Tenant.objects.filter(id__in=tenant_ids).delete()
            
            test_users.delete()
            print("Dados de teste anteriores removidos.")
            
        except Exception as e:
            print(f"Erro limpando dados: {str(e)}")
    
    def create_stress_user(self, user_id):
        """Cria um usuário para teste de stress"""
        try:
            username = f"stressuser_{user_id}"
            email = f"stress{user_id}@example.com"
            cpf = f"987654321{user_id:02d}"
            
            # Criar usuário
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'cpf': cpf,
                    'tipo_pessoa': 'fisica',
                    'first_name': f'Stress User {user_id}'
                }
            )
            
            if created:
                user.set_password('stresspass123')
                user.save()
            
            # Criar tenant
            tenant, tenant_created = Tenant.objects.get_or_create(
                id=user.id + 100,  # Offset para evitar conflitos
                defaults={
                    'nome': f'Stress Tenant {user_id}',
                    'codigo': f'stress_tenant_{user_id}'
                }
            )
            
            # Associar usuário ao tenant
            if not tenant.usuarios.filter(id=user.id).exists():
                tenant.usuarios.add(user)
            
            return user, tenant
            
        except Exception as e:
            with self.lock:
                self.errors.append(f"Erro criando usuário stress {user_id}: {str(e)}")
            return None, None
    
    def create_stress_data(self, user, tenant):
        """Cria dados de teste para stress"""
        try:
            # Criar mais categorias
            categorias = []
            categoria_nomes = [
                ('Alimentação', 'despesa'), ('Transporte', 'despesa'), 
                ('Saúde', 'despesa'), ('Educação', 'despesa'),
                ('Salário', 'receita'), ('Freelance', 'receita'),
                ('Investimentos', 'receita')
            ]
            
            for nome, tipo in categoria_nomes:
                categoria, created = Categoria.objects.get_or_create(
                    nome=f"{nome}_{tenant.id}",
                    tenant_id=tenant.id,
                    defaults={'tipo': tipo}
                )
                categorias.append(categoria)
            
            # Criar mais contas
            contas = []
            conta_nomes = ['Conta Corrente', 'Poupança', 'Carteira', 'Cartão de Crédito']
            for i, nome in enumerate(conta_nomes):
                conta, created = Conta.objects.get_or_create(
                    nome=f"{nome}_{tenant.id}",
                    tenant_id=tenant.id,
                    defaults={
                        'saldo': Decimal(str(random.uniform(500, 5000))),
                        'cor': f'#{random.randint(0, 16777215):06x}'
                    }
                )
                contas.append(conta)
            
            return categorias, contas
            
        except Exception as e:
            with self.lock:
                self.errors.append(f"Erro criando dados stress para usuário {user.username}: {str(e)}")
            return [], []
    
    def intensive_user_operations(self, user_id, num_operations=50):
        """Operações intensivas de um usuário"""
        thread_name = f"StressUser-{user_id}"
        operations_completed = 0
        operations_failed = 0
        operation_times = []
        
        try:
            # Criar usuário e dados
            user, tenant = self.create_stress_user(user_id)
            if not user or not tenant:
                return {
                    'user_id': user_id,
                    'thread': thread_name,
                    'completed': 0,
                    'failed': 1,
                    'avg_time': 0,
                    'error': 'Falha ao criar usuário/tenant'
                }
            
            categorias, contas = self.create_stress_data(user, tenant)
            if not categorias or not contas:
                return {
                    'user_id': user_id,
                    'thread': thread_name,
                    'completed': 0,
                    'failed': 1,
                    'avg_time': 0,
                    'error': 'Falha ao criar dados'
                }
            
            # Operações intensivas
            for i in range(num_operations):
                start_time = time.time()
                try:
                    operation_type = random.choice([
                        'transacao', 'transacao', 'transacao',  # Mais transações
                        'despesa_parcelada', 'consulta', 'update'
                    ])
                    
                    if operation_type == 'transacao':
                        # Múltiplas transações em uma transação DB
                        with transaction.atomic():
                            for _ in range(random.randint(1, 3)):
                                transacao = Transacao.objects.create(
                                    descricao=f"Transação Stress {i+1}-{_} - User {user_id}",
                                    valor=Decimal(str(random.uniform(1, 1000))),
                                    data=f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                                    categoria=random.choice(categorias),
                                    conta=random.choice(contas),
                                    tenant_id=tenant.id,
                                    tipo='despesa' if random.choice(categorias).tipo == 'despesa' else 'receita'
                                )
                    
                    elif operation_type == 'despesa_parcelada':
                        with transaction.atomic():
                            despesa = DespesaParcelada.objects.create(
                                descricao=f"Despesa Stress {i+1} - User {user_id}",
                                valor_total=Decimal(str(random.uniform(200, 2000))),
                                numero_parcelas=random.randint(2, 24),
                                data_primeira_parcela=f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                                categoria=random.choice([c for c in categorias if c.tipo == 'despesa']),
                                conta=random.choice(contas),
                                tenant_id=tenant.id
                            )
                            # Gerar parcelas
                            despesa.gerar_parcelas()
                    
                    elif operation_type == 'consulta':
                        # Consultas complexas
                        transacoes = Transacao.objects.filter(tenant_id=tenant.id).count()
                        despesas = DespesaParcelada.objects.filter(tenant_id=tenant.id).count()
                        # Consulta com agregação
                        from django.db.models import Sum
                        total_valor = Transacao.objects.filter(
                            tenant_id=tenant.id
                        ).aggregate(total=Sum('valor'))['total'] or 0
                    
                    elif operation_type == 'update':
                        # Atualizações
                        transacoes_para_atualizar = Transacao.objects.filter(
                            tenant_id=tenant.id
                        )[:random.randint(1, 5)]
                        
                        for t in transacoes_para_atualizar:
                            t.descricao = f"Atualizada - {t.descricao}"
                            t.save()
                    
                    end_time = time.time()
                    operation_times.append(end_time - start_time)
                    operations_completed += 1
                    
                    # Pausa mínima
                    time.sleep(random.uniform(0.001, 0.01))
                    
                except Exception as e:
                    operations_failed += 1
                    with self.lock:
                        self.errors.append(f"Erro na operação stress {i+1} do usuário {user_id}: {str(e)}")
            
            avg_time = statistics.mean(operation_times) if operation_times else 0
            
            return {
                'user_id': user_id,
                'thread': thread_name,
                'completed': operations_completed,
                'failed': operations_failed,
                'avg_time': avg_time,
                'error': None
            }
            
        except Exception as e:
            return {
                'user_id': user_id,
                'thread': thread_name,
                'completed': operations_completed,
                'failed': operations_failed + 1,
                'avg_time': 0,
                'error': str(e)
            }
    
    def intensive_web_requests(self, user_id, num_requests=20):
        """Requisições web intensivas"""
        try:
            client = Client()
            user = User.objects.get(username=f"stressuser_{user_id}")
            
            # Login
            login_success = client.login(username=user.username, password='stresspass123')
            if not login_success:
                return {
                    'user_id': user_id,
                    'requests_completed': 0,
                    'requests_failed': num_requests,
                    'avg_response_time': 0,
                    'error': 'Falha no login'
                }
            
            requests_completed = 0
            requests_failed = 0
            response_times = []
            
            for i in range(num_requests):
                try:
                    start_time = time.time()
                    
                    # Endpoints mais variados
                    endpoints = [
                        '/dashboard/',
                        '/transacoes/',
                        '/categorias/',
                        '/contas/',
                        '/api/resumo-financeiro/',
                        '/despesas-parceladas/',
                        '/relatorios/'
                    ]
                    
                    endpoint = random.choice(endpoints)
                    response = client.get(endpoint)
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    if response.status_code in [200, 302]:
                        requests_completed += 1
                        response_times.append(response_time)
                    else:
                        requests_failed += 1
                        
                except Exception as e:
                    requests_failed += 1
                    with self.lock:
                        self.errors.append(f"Erro na requisição stress {i+1} do usuário {user_id}: {str(e)}")
            
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            return {
                'user_id': user_id,
                'requests_completed': requests_completed,
                'requests_failed': requests_failed,
                'avg_response_time': avg_response_time,
                'error': None
            }
            
        except Exception as e:
            return {
                'user_id': user_id,
                'requests_completed': 0,
                'requests_failed': num_requests,
                'avg_response_time': 0,
                'error': str(e)
            }
    
    def run_stress_test(self, num_users=10, operations_per_user=50, web_requests_per_user=20):
        """Executa teste de stress"""
        print(f"\n=== TESTE DE STRESS - CONCORRÊNCIA INTENSIVA ===\n")
        print(f"Usuários simultâneos: {num_users}")
        print(f"Operações de BD por usuário: {operations_per_user}")
        print(f"Requisições HTTP por usuário: {web_requests_per_user}")
        print(f"Total de operações esperadas: {num_users * (operations_per_user + web_requests_per_user)}")
        print(f"\nLimpando dados anteriores...")
        
        # Limpar dados anteriores
        self.cleanup_test_data()
        
        print(f"\nIniciando teste de stress...\n")
        start_time = time.time()
        
        # Teste intensivo de operações de BD
        print("1. Executando operações intensivas de banco de dados...")
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            db_futures = {
                executor.submit(self.intensive_user_operations, user_id, operations_per_user): user_id 
                for user_id in range(1, num_users + 1)
            }
            
            db_results = []
            for future in as_completed(db_futures):
                result = future.result()
                db_results.append(result)
                print(f"   Usuário {result['user_id']}: {result['completed']} ops completadas, {result['failed']} falharam, tempo médio: {result['avg_time']:.3f}s")
        
        # Teste intensivo de requisições web
        print("\n2. Executando requisições HTTP intensivas...")
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            web_futures = {
                executor.submit(self.intensive_web_requests, user_id, web_requests_per_user): user_id 
                for user_id in range(1, num_users + 1)
            }
            
            web_results = []
            for future in as_completed(web_futures):
                result = future.result()
                web_results.append(result)
                print(f"   Usuário {result['user_id']}: {result['requests_completed']} reqs completadas, {result['requests_failed']} falharam, tempo médio: {result['avg_response_time']:.3f}s")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Análise detalhada dos resultados
        print(f"\n=== ANÁLISE DETALHADA DOS RESULTADOS ===\n")
        print(f"Tempo total de execução: {total_time:.2f} segundos")
        
        # Estatísticas de BD
        total_db_operations = sum(r['completed'] for r in db_results)
        total_db_failures = sum(r['failed'] for r in db_results)
        avg_db_times = [r['avg_time'] for r in db_results if r['avg_time'] > 0]
        
        print(f"\nOperações de Banco de Dados:")
        print(f"  Total executadas: {total_db_operations}")
        print(f"  Total falharam: {total_db_failures}")
        print(f"  Taxa de sucesso: {(total_db_operations/(total_db_operations+total_db_failures)*100):.1f}%")
        if avg_db_times:
            print(f"  Tempo médio por operação: {statistics.mean(avg_db_times):.3f}s")
            print(f"  Tempo mínimo: {min(avg_db_times):.3f}s")
            print(f"  Tempo máximo: {max(avg_db_times):.3f}s")
        
        # Estatísticas de requisições web
        total_web_requests = sum(r['requests_completed'] for r in web_results)
        total_web_failures = sum(r['requests_failed'] for r in web_results)
        avg_response_times = [r['avg_response_time'] for r in web_results if r['avg_response_time'] > 0]
        
        print(f"\nRequisições HTTP:")
        print(f"  Total executadas: {total_web_requests}")
        print(f"  Total falharam: {total_web_failures}")
        print(f"  Taxa de sucesso: {(total_web_requests/(total_web_requests+total_web_failures)*100):.1f}%")
        if avg_response_times:
            print(f"  Tempo médio de resposta: {statistics.mean(avg_response_times):.3f}s")
            print(f"  Tempo mínimo: {min(avg_response_times):.3f}s")
            print(f"  Tempo máximo: {max(avg_response_times):.3f}s")
        
        # Throughput
        total_operations = total_db_operations + total_web_requests
        throughput = total_operations / total_time
        print(f"\nPerformance Geral:")
        print(f"  Throughput: {throughput:.1f} operações/segundo")
        print(f"  Operações por usuário por segundo: {throughput/num_users:.1f}")
        
        # Verificar isolamento
        print(f"\n=== VERIFICAÇÃO DE ISOLAMENTO ===\n")
        total_records = 0
        for user_id in range(1, num_users + 1):
            try:
                user = User.objects.get(username=f"stressuser_{user_id}")
                tenant = user.tenants.first()
                if tenant:
                    transacoes = Transacao.objects.filter(tenant_id=tenant.id).count()
                    despesas = DespesaParcelada.objects.filter(tenant_id=tenant.id).count()
                    total_records += transacoes + despesas
                    print(f"Usuário {user_id} (Tenant {tenant.id}): {transacoes} transações, {despesas} despesas")
            except Exception as e:
                print(f"Erro verificando usuário {user_id}: {str(e)}")
        
        print(f"\nTotal de registros criados: {total_records}")
        
        # Mostrar erros críticos
        if self.errors:
            print(f"\n=== ERROS ENCONTRADOS ({len(self.errors)}) ===\n")
            error_types = {}
            for error in self.errors:
                error_type = error.split(':')[0] if ':' in error else 'Outros'
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                print(f"  {error_type}: {count} ocorrências")
            
            print(f"\nPrimeiros 5 erros:")
            for error in self.errors[:5]:
                print(f"  - {error}")
        
        # Avaliação final
        print(f"\n=== AVALIAÇÃO FINAL ===\n")
        
        success_rate = (total_operations / (total_operations + total_db_failures + total_web_failures)) * 100
        
        if success_rate >= 99:
            rating = "🏆 EXCELENTE"
            message = "O sistema demonstra excelente capacidade de concorrência!"
        elif success_rate >= 95:
            rating = "✅ MUITO BOM"
            message = "O sistema suporta bem múltiplos usuários simultâneos."
        elif success_rate >= 90:
            rating = "⚠️ BOM"
            message = "O sistema funciona adequadamente, mas há margem para melhorias."
        elif success_rate >= 80:
            rating = "⚠️ REGULAR"
            message = "O sistema apresenta algumas dificuldades com alta concorrência."
        else:
            rating = "❌ PROBLEMÁTICO"
            message = "O sistema tem sérios problemas de concorrência."
        
        print(f"{rating}: {message}")
        print(f"Taxa de sucesso geral: {success_rate:.1f}%")
        print(f"Throughput: {throughput:.1f} ops/seg")
        
        if throughput > 50:
            print("🚀 Performance excelente para aplicação web!")
        elif throughput > 20:
            print("👍 Performance adequada para uso comercial.")
        else:
            print("⚠️ Performance pode ser limitante em alta demanda.")
        
        return {
            'success_rate': success_rate,
            'throughput': throughput,
            'total_time': total_time,
            'total_operations': total_operations,
            'total_failures': total_db_failures + total_web_failures
        }

if __name__ == '__main__':
    print("Teste de Stress - Concorrência Intensiva")
    print("========================================\n")
    
    tester = StressConcurrentTest()
    
    # Configurações mais intensivas
    NUM_USERS = 10  # Mais usuários
    OPERATIONS_PER_USER = 30  # Mais operações
    WEB_REQUESTS_PER_USER = 15  # Mais requisições
    
    try:
        results = tester.run_stress_test(
            num_users=NUM_USERS,
            operations_per_user=OPERATIONS_PER_USER,
            web_requests_per_user=WEB_REQUESTS_PER_USER
        )
        
        print(f"\n🎯 Teste de stress concluído!")
        print(f"Resultado: {results['success_rate']:.1f}% de sucesso com {results['throughput']:.1f} ops/seg")
        
    except Exception as e:
        print(f"\nErro durante o teste de stress: {str(e)}")
        import traceback
        traceback.print_exc()