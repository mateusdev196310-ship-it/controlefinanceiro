import os
import django
import sqlite3
import psycopg2
from datetime import datetime
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeiro.settings')
django.setup()

from financas.models import Categoria, Banco, Conta, Transacao, DespesaParcelada, FechamentoMensal, ConfiguracaoFechamento

def migrate_data():
    try:
        # Conectar ao SQLite
        sqlite_conn = sqlite3.connect('db.sqlite3')
        sqlite_cursor = sqlite_conn.cursor()
        
        print("Iniciando migração de dados do SQLite para PostgreSQL...")
        
        # Migrar Categorias
        print("Migrando categorias...")
        sqlite_cursor.execute("SELECT * FROM financas_categoria")
        categorias = sqlite_cursor.fetchall()
        
        for cat in categorias:
            categoria, created = Categoria.objects.get_or_create(
                id=cat[0],
                defaults={
                    'nome': cat[1],
                    'tipo': cat[2] if len(cat) > 2 else 'DESPESA'
                }
            )
            if created:
                print(f"Categoria criada: {categoria.nome}")
        
        # Migrar Bancos
        print("Migrando bancos...")
        sqlite_cursor.execute("SELECT * FROM financas_banco")
        bancos = sqlite_cursor.fetchall()
        
        for banco_data in bancos:
            try:
                # Verificar se o banco tem código, se não tiver, gerar um
                codigo = banco_data[2] if len(banco_data) > 2 and banco_data[2] else f"B{banco_data[0]:03d}"
                
                banco, created = Banco.objects.get_or_create(
                    id=banco_data[0],
                    defaults={
                        'nome': banco_data[1],
                        'codigo': codigo,
                        'imagem': banco_data[3] if len(banco_data) > 3 else None
                    }
                )
                if created:
                    print(f"Banco criado: {banco.nome} ({banco.codigo})")
            except Exception as e:
                print(f"Erro ao migrar banco {banco_data[1]}: {e}")
        
        # Migrar Contas
        print("Migrando contas...")
        sqlite_cursor.execute("SELECT * FROM financas_conta")
        contas = sqlite_cursor.fetchall()
        
        for conta_data in contas:
            try:
                banco = Banco.objects.get(id=conta_data[2]) if conta_data[2] else None
                conta, created = Conta.objects.get_or_create(
                    id=conta_data[0],
                    defaults={
                        'nome': conta_data[1],
                        'banco': banco,
                        'saldo_inicial': conta_data[3] if len(conta_data) > 3 else 0,
                        'saldo_inicial_lancado': conta_data[4] if len(conta_data) > 4 else False
                    }
                )
                if created:
                    print(f"Conta criada: {conta.nome}")
            except Exception as e:
                print(f"Erro ao migrar conta {conta_data[1]}: {e}")
        
        # Migrar Transações
        print("Migrando transações...")
        sqlite_cursor.execute("SELECT * FROM financas_transacao")
        transacoes = sqlite_cursor.fetchall()
        
        for trans in transacoes:
            try:
                categoria = Categoria.objects.get(id=trans[3]) if trans[3] else None
                conta = Conta.objects.get(id=trans[11]) if len(trans) > 11 and trans[11] else None
                
                # Converter data
                data = datetime.strptime(trans[2], '%Y-%m-%d').date() if trans[2] else None
                data_pagamento = None
                if len(trans) > 13 and trans[13]:
                    try:
                        data_pagamento = datetime.strptime(trans[13], '%Y-%m-%d').date()
                    except:
                        pass
                
                transacao, created = Transacao.objects.get_or_create(
                    id=trans[0],
                    defaults={
                        'descricao': trans[1],
                        'data': data,
                        'categoria': categoria,
                        'valor': trans[4],
                        'tipo': trans[5],
                        'eh_parcelada': trans[6] if len(trans) > 6 else False,
                        'numero_parcela': trans[7] if len(trans) > 7 else None,
                        'total_parcelas': trans[8] if len(trans) > 8 else None,
                        'valor_parcela': trans[9] if len(trans) > 9 else None,
                        'parcela_atual': trans[10] if len(trans) > 10 else None,
                        'conta': conta,
                        'pago': trans[12] if len(trans) > 12 else False,
                        'data_pagamento': data_pagamento
                    }
                )
                if created:
                    print(f"Transação criada: {transacao.descricao}")
            except Exception as e:
                print(f"Erro ao migrar transação {trans[1]}: {e}")
        
        # Migrar Despesas Parceladas
        print("Migrando despesas parceladas...")
        try:
            sqlite_cursor.execute("SELECT * FROM financas_despesaparcelada")
            despesas = sqlite_cursor.fetchall()
            
            for desp in despesas:
                try:
                    categoria = Categoria.objects.get(id=desp[2]) if desp[2] else None
                    conta = Conta.objects.get(id=desp[7]) if len(desp) > 7 and desp[7] else None
                    
                    data = datetime.strptime(desp[3], '%Y-%m-%d').date() if desp[3] else None
                    
                    despesa, created = DespesaParcelada.objects.get_or_create(
                        id=desp[0],
                        defaults={
                            'descricao': desp[1],
                            'categoria': categoria,
                            'data_primeira_parcela': data,
                            'valor_total': desp[4],
                            'numero_parcelas': desp[5],
                            'valor_parcela': desp[6],
                            'conta': conta
                        }
                    )
                    if created:
                        print(f"Despesa parcelada criada: {despesa.descricao}")
                except Exception as e:
                    print(f"Erro ao migrar despesa parcelada {desp[1]}: {e}")
        except sqlite3.OperationalError:
            print("Tabela de despesas parceladas não encontrada, pulando...")
        
        # Migrar Fechamentos Mensais
        print("Migrando fechamentos mensais...")
        try:
            sqlite_cursor.execute("SELECT * FROM financas_fechamentomensal")
            fechamentos = sqlite_cursor.fetchall()
            
            for fech in fechamentos:
                try:
                    data_inicio = datetime.strptime(fech[1], '%Y-%m-%d').date() if fech[1] else None
                    data_fim = datetime.strptime(fech[2], '%Y-%m-%d').date() if fech[2] else None
                    data_fim_periodo = None
                    if len(fech) > 6 and fech[6]:
                        try:
                            data_fim_periodo = datetime.strptime(fech[6], '%Y-%m-%d').date()
                        except:
                            pass
                    
                    fechamento, created = FechamentoMensal.objects.get_or_create(
                        id=fech[0],
                        defaults={
                            'data_inicio': data_inicio,
                            'data_fim': data_fim,
                            'saldo_inicial': fech[3],
                            'total_receitas': fech[4],
                            'total_despesas': fech[5],
                            'data_fim_periodo': data_fim_periodo
                        }
                    )
                    if created:
                        print(f"Fechamento mensal criado: {fechamento.data_inicio} - {fechamento.data_fim}")
                except Exception as e:
                    print(f"Erro ao migrar fechamento mensal: {e}")
        except sqlite3.OperationalError:
            print("Tabela de fechamentos mensais não encontrada, pulando...")
        
        # Migrar Configurações de Fechamento
        print("Migrando configurações de fechamento...")
        try:
            sqlite_cursor.execute("SELECT * FROM financas_configuracaofechamento")
            configs = sqlite_cursor.fetchall()
            
            for config in configs:
                try:
                    configuracao, created = ConfiguracaoFechamento.objects.get_or_create(
                        id=config[0],
                        defaults={
                            'dia_fechamento': config[1],
                            'ativo': config[2]
                        }
                    )
                    if created:
                        print(f"Configuração de fechamento criada: dia {configuracao.dia_fechamento}")
                except Exception as e:
                    print(f"Erro ao migrar configuração de fechamento: {e}")
        except sqlite3.OperationalError:
            print("Tabela de configurações de fechamento não encontrada, pulando...")
        
        sqlite_conn.close()
        print("\nMigração de dados concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"Erro durante a migração: {e}")
        return False

if __name__ == '__main__':
    success = migrate_data()
    sys.exit(0 if success else 1)