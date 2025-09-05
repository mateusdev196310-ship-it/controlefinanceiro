#!/usr/bin/env python
"""
Teste de Concorrência - Múltiplos Usuários Simultâneos
Este script testa se o sistema suporta múltiplos usuários fazendo requisições simultâneas
"""

import os
import sys
import django
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

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

class ConcurrentUserTest:
    def __init__(self):
        self.results = []
        self.errors = []
        self.lock = threading.Lock()
        
    def create_test_user(self, user_id):
        """Cria um usuário de teste"""
        try:
            username = f"testuser_{user_id}"
            email = f"test{user_id}@example.com"
            cpf = f"123456789{user_id:02d}"
            
            # Criar usuário
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'cpf': cpf,
                    'tipo_pessoa': 'fisica',
                    'first_name': f'Test User {user_id}'
                }
            )
            
            if created:
                user.set_password('testpass123')
                user.save()
            
            # Criar tenant
            tenant, tenant_created = Tenant.objects.get_or_create(
                id=user.id,
                defaults={
                    'nome': f'Tenant {user_id}',
                    'codigo': f'tenant_{user_id}'
                }
            )
            
            # Associar usuário ao tenant
            if not tenant.usuarios.filter(id=user.id).exists():
                tenant.usuarios.add(user)
            
            return user, tenant
            
        except Exception as e:
            with self.lock:
                self.errors.append(f"Erro criando usuário {user_id}: {str(e)}")
            return None, None
    
    def create_test_data(self, user, tenant):
        """Cria dados de teste para um usuário"""
        try:
            # Criar categorias
            categorias = []
            for i, nome in enumerate(['Alimentação', 'Transporte', 'Salário'], 1):
                categoria, created = Categoria.objects.get_or_create(
                    nome=nome,
                    tenant_id=tenant.id,
                    defaults={'tipo': 'despesa' if i <= 2 else 'receita'}
                )
                categorias.append(categoria)
            
            # Criar contas
            contas = []
            for i, nome in enumerate(['Conta Corrente', 'Carteira'], 1):
                conta, created = Conta.objects.get_or_create(
                    nome=nome,
                    tenant_id=tenant.id,
                    defaults={
                        'saldo': Decimal('1000.00'),
                        'cor': '#007bff' if i == 1 else '#28a745'
                    }
                )
                contas.append(conta)
            
            return categorias, contas
            
        except Exception as e:
            with self.lock:
                self.errors.append(f"Erro criando dados para usuário {user.username}: {str(e)}")
            return [], []
    
    def simulate_user_operations(self, user_id, num_operations=10):
        """Simula operações de um usuário específico"""
        thread_name = f"User-{user_id}"
        operations_completed = 0
        operations_failed = 0
        
        try:
            # Criar usuário e dados de teste
            user, tenant = self.create_test_user(user_id)
            if not user or not tenant:
                return {
                    'user_id': user_id,
                    'thread': thread_name,
                    'completed': 0,
                    'failed': 1,
                    'error': 'Falha ao criar usuário/tenant'
                }
            
            categorias, contas = self.create_test_data(user, tenant)
            if not categorias or not contas:
                return {
                    'user_id': user_id,
                    'thread': thread_name,
                    'completed': 0,
                    'failed': 1,
                    'error': 'Falha ao criar dados de teste'
                }
            
            # Simular operações
            for i in range(num_operations):
                try:
                    operation_type = random.choice(['transacao', 'despesa_parcelada', 'consulta'])
                    
                    if operation_type == 'transacao':
                        # Criar transação
                        with transaction.atomic():
                            transacao = Transacao.objects.create(
                                descricao=f"Transação {i+1} - User {user_id}",
                                valor=Decimal(str(random.uniform(10, 500))),
                                data=f"2024-01-{random.randint(1, 28):02d}",
                                categoria=random.choice(categorias),
                                conta=random.choice(contas),
                                tenant_id=tenant.id
                            )
                    
                    elif operation_type == 'despesa_parcelada':
                        # Criar despesa parcelada
                        with transaction.atomic():
                            despesa = DespesaParcelada.objects.create(
                                descricao=f"Despesa Parcelada {i+1} - User {user_id}",
                                valor_total=Decimal(str(random.uniform(100, 1000))),
                                numero_parcelas=random.randint(2, 12),
                                data_primeira_parcela=f"2024-01-{random.randint(1, 28):02d}",
                                categoria=random.choice([c for c in categorias if c.tipo == 'despesa']),
                                conta=random.choice(contas),
                                tenant_id=tenant.id
                            )
                    
                    elif operation_type == 'consulta':
                        # Fazer consultas
                        transacoes = Transacao.objects.filter(tenant_id=tenant.id).count()
                        despesas = DespesaParcelada.objects.filter(tenant_id=tenant.id).count()
                    
                    operations_completed += 1
                    
                    # Pequena pausa para simular tempo de processamento
                    time.sleep(random.uniform(0.01, 0.05))
                    
                except Exception as e:
                    operations_failed += 1
                    with self.lock:
                        self.errors.append(f"Erro na operação {i+1} do usuário {user_id}: {str(e)}")
            
            return {
                'user_id': user_id,
                'thread': thread_name,
                'completed': operations_completed,
                'failed': operations_failed,
                'error': None
            }
            
        except Exception as e:
            return {
                'user_id': user_id,
                'thread': thread_name,
                'completed': operations_completed,
                'failed': operations_failed + 1,
                'error': str(e)
            }
    
    def test_web_requests(self, user_id, num_requests=5):
        """Testa requisições HTTP simultâneas"""
        try:
            client = Client()
            user = User.objects.get(username=f"testuser_{user_id}")
            
            # Login
            login_success = client.login(username=user.username, password='testpass123')
            if not login_success:
                return {
                    'user_id': user_id,
                    'requests_completed': 0,
                    'requests_failed': num_requests,
                    'error': 'Falha no login'
                }
            
            requests_completed = 0
            requests_failed = 0
            
            for i in range(num_requests):
                try:
                    # Testar diferentes endpoints
                    endpoints = [
                        '/dashboard/',
                        '/transacoes/',
                        '/categorias/',
                        '/contas/',
                        '/api/resumo-financeiro/'
                    ]
                    
                    endpoint = random.choice(endpoints)
                    response = client.get(endpoint)
                    
                    if response.status_code in [200, 302]:
                        requests_completed += 1
                    else:
                        requests_failed += 1
                        
                except Exception as e:
                    requests_failed += 1
                    with self.lock:
                        self.errors.append(f"Erro na requisição {i+1} do usuário {user_id}: {str(e)}")
            
            return {
                'user_id': user_id,
                'requests_completed': requests_completed,
                'requests_failed': requests_failed,
                'error': None
            }
            
        except Exception as e:
            return {
                'user_id': user_id,
                'requests_completed': 0,
                'requests_failed': num_requests,
                'error': str(e)
            }
    
    def run_concurrent_test(self, num_users=5, operations_per_user=10, web_requests_per_user=5):
        """Executa teste de concorrência"""
        print(f"\n=== TESTE DE CONCORRÊNCIA ===\n")
        print(f"Usuários simultâneos: {num_users}")
        print(f"Operações por usuário: {operations_per_user}")
        print(f"Requisições web por usuário: {web_requests_per_user}")
        print(f"\nIniciando teste...\n")
        
        start_time = time.time()
        
        # Teste de operações de banco de dados
        print("1. Testando operações de banco de dados simultâneas...")
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            db_futures = {
                executor.submit(self.simulate_user_operations, user_id, operations_per_user): user_id 
                for user_id in range(1, num_users + 1)
            }
            
            db_results = []
            for future in as_completed(db_futures):
                result = future.result()
                db_results.append(result)
                print(f"   Usuário {result['user_id']}: {result['completed']} operações completadas, {result['failed']} falharam")
        
        # Teste de requisições web
        print("\n2. Testando requisições HTTP simultâneas...")
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            web_futures = {
                executor.submit(self.test_web_requests, user_id, web_requests_per_user): user_id 
                for user_id in range(1, num_users + 1)
            }
            
            web_results = []
            for future in as_completed(web_futures):
                result = future.result()
                web_results.append(result)
                print(f"   Usuário {result['user_id']}: {result['requests_completed']} requisições completadas, {result['requests_failed']} falharam")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Relatório final
        print(f"\n=== RELATÓRIO FINAL ===\n")
        print(f"Tempo total: {total_time:.2f} segundos")
        
        # Estatísticas de operações DB
        total_db_operations = sum(r['completed'] for r in db_results)
        total_db_failures = sum(r['failed'] for r in db_results)
        print(f"\nOperações de Banco de Dados:")
        print(f"  Total executadas: {total_db_operations}")
        print(f"  Total falharam: {total_db_failures}")
        print(f"  Taxa de sucesso: {(total_db_operations/(total_db_operations+total_db_failures)*100):.1f}%")
        
        # Estatísticas de requisições web
        total_web_requests = sum(r['requests_completed'] for r in web_results)
        total_web_failures = sum(r['requests_failed'] for r in web_results)
        print(f"\nRequisições HTTP:")
        print(f"  Total executadas: {total_web_requests}")
        print(f"  Total falharam: {total_web_failures}")
        print(f"  Taxa de sucesso: {(total_web_requests/(total_web_requests+total_web_failures)*100):.1f}%")
        
        # Verificar isolamento de dados
        print(f"\n=== VERIFICAÇÃO DE ISOLAMENTO DE DADOS ===\n")
        for user_id in range(1, num_users + 1):
            try:
                user = User.objects.get(username=f"testuser_{user_id}")
                # Buscar tenant associado ao usuário
                tenant = user.tenants.first()
                if tenant:
                    tenant_transacoes = Transacao.objects.filter(tenant_id=tenant.id).count()
                    tenant_despesas = DespesaParcelada.objects.filter(tenant_id=tenant.id).count()
                    print(f"Usuário {user_id} (Tenant {tenant.id}): {tenant_transacoes} transações, {tenant_despesas} despesas parceladas")
                else:
                    print(f"Usuário {user_id}: Nenhum tenant associado")
            except Exception as e:
                print(f"Erro verificando usuário {user_id}: {str(e)}")
        
        # Mostrar erros se houver
        if self.errors:
            print(f"\n=== ERROS ENCONTRADOS ({len(self.errors)}) ===\n")
            for error in self.errors[:10]:  # Mostrar apenas os primeiros 10 erros
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... e mais {len(self.errors) - 10} erros")
        
        # Conclusão
        print(f"\n=== CONCLUSÃO ===\n")
        if total_db_failures == 0 and total_web_failures == 0:
            print("✅ SUCESSO: O sistema suporta múltiplos usuários simultâneos sem problemas!")
        elif (total_db_failures + total_web_failures) < (total_db_operations + total_web_requests) * 0.05:
            print("⚠️  PARCIAL: O sistema funciona bem com múltiplos usuários, mas há algumas falhas ocasionais.")
        else:
            print("❌ PROBLEMAS: O sistema apresenta dificuldades com múltiplos usuários simultâneos.")
        
        print(f"\nThroughput: {(total_db_operations + total_web_requests)/total_time:.1f} operações/segundo")
        
        return {
            'success': total_db_failures == 0 and total_web_failures == 0,
            'total_time': total_time,
            'db_operations': total_db_operations,
            'db_failures': total_db_failures,
            'web_requests': total_web_requests,
            'web_failures': total_web_failures,
            'throughput': (total_db_operations + total_web_requests)/total_time
        }

if __name__ == '__main__':
    # Executar teste
    tester = ConcurrentUserTest()
    
    print("Teste de Concorrência - Sistema Financeiro")
    print("==========================================\n")
    
    # Configurações do teste
    NUM_USERS = 5  # Número de usuários simultâneos
    OPERATIONS_PER_USER = 8  # Operações de DB por usuário
    WEB_REQUESTS_PER_USER = 5  # Requisições HTTP por usuário
    
    try:
        results = tester.run_concurrent_test(
            num_users=NUM_USERS,
            operations_per_user=OPERATIONS_PER_USER,
            web_requests_per_user=WEB_REQUESTS_PER_USER
        )
        
        print(f"\nTeste concluído com sucesso!")
        
    except Exception as e:
        print(f"\nErro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()