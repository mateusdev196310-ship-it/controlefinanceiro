"""Serviços de negócio para a aplicação financas.

Este módulo contém as classes de serviço que centralizam a lógica de negócio,
separando-a das views e models para melhor organização e testabilidade.
"""

from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from .utils import validar_data_futura
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import logging
import time

from .models import Conta, Transacao
from .constants import TipoTransacao, ErrorMessages, SuccessMessages
from .exceptions import ContaServiceError, TransacaoServiceError
from .logging_config import get_logger

logger = get_logger('financas.services')

class ContaService:
    """Serviço para operações relacionadas a contas."""
    
    @staticmethod
    def criar_conta(nome, saldo_inicial=None):
        """
        Cria uma nova conta com validações de negócio.
        
        Args:
            nome (str): Nome da conta
            saldo_inicial (Decimal, optional): Saldo inicial da conta
            
        Returns:
            Conta: A conta criada
            
        Raises:
            ContaServiceError: Se houver erro na criação
        """
        start_time = time.time()
        
        try:
            with transaction.atomic():
                conta = Conta.objects.create(
                    nome=nome,
                    saldo=saldo_inicial or Decimal('0.00')
                )
                
                # Log estruturado de sucesso
                duration_ms = int((time.time() - start_time) * 1000)
                logger.log_operation(
                    level=logging.INFO,
                    operation='CREATE_CONTA',
                    entity_type='Conta',
                    entity_id=conta.id,
                    message=f"Conta criada: {conta.nome}",
                    duration_ms=duration_ms,
                    nome=conta.nome,
                    saldo_inicial=float(conta.saldo)
                )
                
                return conta
                
        except Exception as e:
            logger.log_error(
                operation='CREATE_CONTA',
                error=e,
                entity_type='Conta',
                error_code='CREATION_ERROR',
                nome=nome,
                saldo_inicial=float(saldo_inicial or Decimal('0.00'))
            )
            raise ContaServiceError(f"Erro ao criar conta: {str(e)}")
    
    @staticmethod
    def atualizar_saldo_conta(conta_id):
        """
        Atualiza o saldo de uma conta baseado em suas transações.
        
        Args:
            conta_id (int): ID da conta
            
        Returns:
            Decimal: O novo saldo da conta
            
        Raises:
            ContaServiceError: Se a conta não existir ou houver erro
        """
        start_time = time.time()
        
        try:
            conta = Conta.objects.get(id=conta_id)
            saldo_anterior = conta.saldo
            conta.atualizar_saldo()
            
            # Log estruturado de sucesso
            duration_ms = int((time.time() - start_time) * 1000)
            logger.log_operation(
                level=logging.INFO,
                operation='UPDATE_SALDO',
                entity_type='Conta',
                entity_id=conta_id,
                message=f"Saldo atualizado - Conta: {conta.nome}",
                duration_ms=duration_ms,
                saldo_anterior=float(saldo_anterior),
                novo_saldo=float(conta.saldo),
                diferenca=float(conta.saldo - saldo_anterior)
            )
            
            return conta.saldo
            
        except Conta.DoesNotExist:
            logger.log_error(
                operation='UPDATE_SALDO',
                error=f"Conta com ID {conta_id} não encontrada",
                entity_type='Conta',
                entity_id=conta_id,
                error_code='CONTA_NOT_FOUND'
            )
            raise ContaServiceError(ErrorMessages.CONTA_INEXISTENTE)
        except Exception as e:
            logger.log_error(
                operation='UPDATE_SALDO',
                error=e,
                entity_type='Conta',
                entity_id=conta_id,
                error_code='UPDATE_ERROR'
            )
            raise ContaServiceError(f"Erro ao atualizar saldo: {str(e)}")
    
    @staticmethod
    def obter_resumo_financeiro(conta_id, mes=None, ano=None):
        """
        Obtém resumo financeiro de uma conta para um período específico.
        
        Args:
            conta_id (int): ID da conta
            mes (int, optional): Mês para filtrar (1-12)
            ano (int, optional): Ano para filtrar
            
        Returns:
            dict: Resumo com receitas, despesas, saldo anterior e atual
        """
        start_time = time.time()
        
        try:
            conta = Conta.objects.get(id=conta_id)
            
            # Se não especificado, usar mês/ano atual
            if mes is None or ano is None:
                hoje = timezone.now().date()
                mes = mes or hoje.month
                ano = ano or hoje.year
            
            # Filtrar transações do período (EXCLUINDO despesas parceladas)
            transacoes_periodo = Transacao.objects.filter(
                conta=conta,
                data__month=mes,
                data__year=ano,
                despesa_parcelada__isnull=True  # Excluir despesas parceladas
            )
            
            # Calcular receitas e despesas do período
            receitas = transacoes_periodo.filter(
                tipo=TipoTransacao.RECEITA
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            
            despesas = transacoes_periodo.filter(
                tipo__in=TipoTransacao.get_expense_types()
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            
            # Calcular saldo anterior (receitas - despesas dos meses anteriores) EXCLUINDO despesas parceladas
            transacoes_anteriores = Transacao.objects.filter(
                conta=conta,
                data__lt=date(ano, mes, 1),
                despesa_parcelada__isnull=True  # Excluir despesas parceladas
            )
            
            receitas_anteriores = transacoes_anteriores.filter(
                tipo=TipoTransacao.RECEITA
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            
            despesas_anteriores = transacoes_anteriores.filter(
                tipo__in=TipoTransacao.get_expense_types()
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            
            saldo_anterior = receitas_anteriores - despesas_anteriores
            movimento_mes = receitas - despesas
            saldo_atual = saldo_anterior + movimento_mes
            
            resumo = {
                'conta': conta,
                'periodo': f"{mes:02d}/{ano}",
                'receitas': receitas,
                'despesas': despesas,
                'movimento_mes': movimento_mes,
                'saldo_anterior': saldo_anterior,
                'saldo_atual': saldo_atual,
                'total_transacoes': transacoes_periodo.count()
            }
            
            # Log estruturado de sucesso
            duration_ms = int((time.time() - start_time) * 1000)
            logger.log_operation(
                level=logging.INFO,
                operation='GET_FINANCIAL_SUMMARY',
                entity_type='Conta',
                entity_id=conta_id,
                message=f"Resumo financeiro gerado para conta {conta.nome} - {mes:02d}/{ano}",
                duration_ms=duration_ms,
                periodo=f"{mes:02d}/{ano}",
                receitas=float(receitas),
                despesas=float(despesas),
                movimento_mes=float(movimento_mes),
                total_transacoes=transacoes_periodo.count()
            )
            
            return resumo
            
        except Conta.DoesNotExist:
            logger.log_error(
                operation='GET_FINANCIAL_SUMMARY',
                error=f"Conta com ID {conta_id} não encontrada",
                entity_type='Conta',
                entity_id=conta_id,
                error_code='CONTA_NOT_FOUND'
            )
            raise ContaServiceError(ErrorMessages.CONTA_INEXISTENTE)
        except Exception as e:
            logger.log_error(
                operation='GET_FINANCIAL_SUMMARY',
                error=e,
                entity_type='Conta',
                entity_id=conta_id,
                error_code='UNEXPECTED_ERROR'
            )
            raise ContaServiceError(f"Erro ao gerar resumo: {str(e)}")

class TransacaoService:
    """Serviço para operações relacionadas a transações."""
    
    @staticmethod
    def criar_transacao(conta_id, descricao, valor, tipo, data=None, categoria=None):
        """
        Cria uma nova transação com validações de negócio.
        
        Args:
            conta_id (int): ID da conta
            descricao (str): Descrição da transação
            valor (Decimal): Valor da transação
            tipo (str): Tipo da transação (receita/despesa)
            data (date, optional): Data da transação
            categoria (str, optional): Categoria da transação
            
        Returns:
            Transacao: A transação criada
            
        Raises:
            TransacaoServiceError: Se houver erro na criação
        """
        start_time = time.time()
        
        try:
            with transaction.atomic():
                conta = Conta.objects.get(id=conta_id)
                
                # Validações de negócio
                if valor <= 0:
                    raise TransacaoServiceError(ErrorMessages.VALOR_ZERO)
                
                if not TipoTransacao.is_valid_type(tipo):
                    raise TransacaoServiceError(ErrorMessages.TIPO_INVALIDO)
                
                # Validação de data futura
                if validar_data_futura(data):
                    raise TransacaoServiceError(ErrorMessages.DATA_FUTURA)
                
                # Buscar categoria se fornecida
                categoria_obj = None
                if categoria:
                    from .models import Categoria
                    try:
                        categoria_obj = Categoria.objects.get(nome=categoria)
                    except Categoria.DoesNotExist:
                        raise TransacaoServiceError(f"Categoria '{categoria}' não encontrada")
                
                # Criar transação
                transacao = Transacao.objects.create(
                    conta=conta,
                    descricao=descricao,
                    valor=valor,
                    tipo=tipo,
                    data=data or timezone.now().date(),
                    categoria=categoria_obj
                )
                
                # Log estruturado de sucesso
                duration_ms = int((time.time() - start_time) * 1000)
                logger.log_operation(
                    level=logging.INFO,
                    operation='CREATE_TRANSACAO',
                    entity_type='Transacao',
                    entity_id=transacao.id,
                    message=f"Transação criada: {transacao.descricao}",
                    duration_ms=duration_ms,
                    conta_id=conta_id,
                    conta_nome=conta.nome,
                    descricao=descricao,
                    valor=float(valor),
                    tipo=tipo,
                    categoria=categoria
                )
                
                return transacao
                
        except Conta.DoesNotExist:
            logger.log_error(
                operation='CREATE_TRANSACAO',
                error=f"Conta com ID {conta_id} não encontrada",
                entity_type='Transacao',
                error_code='CONTA_NOT_FOUND',
                conta_id=conta_id
            )
            raise TransacaoServiceError(ErrorMessages.CONTA_INEXISTENTE)
        except Exception as e:
            logger.log_error(
                operation='CREATE_TRANSACAO',
                error=e,
                entity_type='Transacao',
                error_code='CREATION_ERROR',
                conta_id=conta_id,
                descricao=descricao,
                valor=float(valor) if valor else None,
                tipo=tipo
            )
            raise TransacaoServiceError(f"Erro ao criar transação: {str(e)}")
    
    @staticmethod
    def obter_transacoes_periodo(conta_id, data_inicio, data_fim):
        """
        Obtém transações de uma conta em um período específico.
        
        Args:
            conta_id (int): ID da conta
            data_inicio (date): Data de início do período
            data_fim (date): Data de fim do período
            
        Returns:
            QuerySet: Transações do período ordenadas por data
        """
        start_time = time.time()
        
        try:
            queryset = Transacao.objects.filter(
                conta_id=conta_id,
                data__range=[data_inicio, data_fim]
            ).order_by('-data', '-id')
            
            total_transacoes = queryset.count()
            
            # Log estruturado de sucesso
            duration_ms = int((time.time() - start_time) * 1000)
            logger.log_operation(
                level=logging.INFO,
                operation='GET_TRANSACOES_PERIODO',
                entity_type='Transacao',
                message=f"Transações do período obtidas para conta {conta_id}",
                duration_ms=duration_ms,
                conta_id=conta_id,
                data_inicio=data_inicio.isoformat(),
                data_fim=data_fim.isoformat(),
                total_transacoes=total_transacoes
            )
            
            return queryset
            
        except Exception as e:
            logger.log_error(
                operation='GET_TRANSACOES_PERIODO',
                error=e,
                entity_type='Transacao',
                error_code='QUERY_ERROR',
                conta_id=conta_id,
                data_inicio=data_inicio.isoformat() if data_inicio else None,
                data_fim=data_fim.isoformat() if data_fim else None
            )
            raise TransacaoServiceError(f"Erro ao obter transações: {str(e)}")
    
    @staticmethod
    def calcular_totalizadores(queryset):
        """
        Calcula os totalizadores para um queryset de transações.
        
        Args:
            queryset: QuerySet de transações
            
        Returns:
            dict: Dicionário com os totalizadores
        """
        try:
            # Calcular totais por tipo
            total_receitas = queryset.filter(tipo=TipoTransacao.RECEITA).aggregate(
                total=Sum('valor')
            )['total'] or Decimal('0.00')
            
            total_despesas = queryset.filter(tipo__in=TipoTransacao.get_expense_types()).aggregate(
                total=Sum('valor')
            )['total'] or Decimal('0.00')
            
            saldo_liquido = total_receitas - total_despesas
            total_transacoes = queryset.count()
            
            return {
                'total_receitas': total_receitas,
                'total_despesas': total_despesas,
                'saldo_liquido': saldo_liquido,
                'total_transacoes': total_transacoes
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular totalizadores: {str(e)}")
            return {
                'total_receitas': Decimal('0.00'),
                'total_despesas': Decimal('0.00'),
                'saldo_liquido': Decimal('0.00'),
                'total_transacoes': 0
            }
    
    @staticmethod
    def listar_transacoes_com_filtros(**filtros):
        """
        Lista transações aplicando filtros dinâmicos.
        
        Args:
            **filtros: Filtros a serem aplicados
                - data_inicio (str): Data de início no formato YYYY-MM-DD
                - data_fim (str): Data de fim no formato YYYY-MM-DD
                - categoria_id (str): ID da categoria
                - tipo (str): Tipo da transação
                - responsavel (str): Nome do responsável (busca parcial)
                - descricao (str): Descrição (busca parcial)
                
        Returns:
            QuerySet: Transações filtradas ordenadas por data
            
        Raises:
            TransacaoServiceError: Se houver erro na consulta
        """
        start_time = time.time()
        
        try:
            queryset = Transacao.objects.select_related('conta', 'categoria')
            filtros_aplicados = 0
            
            # Aplicar filtros dinamicamente
            if 'data_inicio' in filtros and filtros['data_inicio']:
                try:
                    data_inicio = datetime.strptime(filtros['data_inicio'], '%Y-%m-%d').date()
                    queryset = queryset.filter(data__gte=data_inicio)
                    filtros_aplicados += 1
                except ValueError:
                    logger.warning(f"Data de início inválida: {filtros['data_inicio']}")
            
            if 'data_fim' in filtros and filtros['data_fim']:
                try:
                    data_fim = datetime.strptime(filtros['data_fim'], '%Y-%m-%d').date()
                    queryset = queryset.filter(data__lte=data_fim)
                    filtros_aplicados += 1
                except ValueError:
                    logger.warning(f"Data de fim inválida: {filtros['data_fim']}")
            
            if 'categoria_id' in filtros and filtros['categoria_id']:
                try:
                    categoria_id = int(filtros['categoria_id'])
                    queryset = queryset.filter(categoria_id=categoria_id)
                    filtros_aplicados += 1
                except (ValueError, TypeError):
                    logger.warning(f"ID de categoria inválido: {filtros['categoria_id']}")
            
            if 'tipo' in filtros and filtros['tipo']:
                if TipoTransacao.is_valid_type(filtros['tipo']):
                    queryset = queryset.filter(tipo=filtros['tipo'])
                    filtros_aplicados += 1
                else:
                    logger.warning(f"Tipo de transação inválido: {filtros['tipo']}")
            
            if 'responsavel' in filtros and filtros['responsavel']:
                queryset = queryset.filter(responsavel__icontains=filtros['responsavel'])
                filtros_aplicados += 1
            
            if 'descricao' in filtros and filtros['descricao']:
                queryset = queryset.filter(descricao__icontains=filtros['descricao'])
                filtros_aplicados += 1
            
            # Ordenar por data decrescente
            queryset = queryset.order_by('-data', '-id')
            
            # Contar resultados para métricas
            total_resultados = queryset.count()
            
            # Log estruturado de sucesso
            duration_ms = int((time.time() - start_time) * 1000)
            logger.log_operation(
                level=logging.INFO,
                operation='LIST_TRANSACOES_FILTERED',
                entity_type='Transacao',
                message=f"Consulta de transações executada com {filtros_aplicados} filtros",
                duration_ms=duration_ms,
                filtros_aplicados=filtros_aplicados,
                total_resultados=total_resultados,
                filtros=filtros
            )
            
            return queryset
            
        except Exception as e:
            logger.log_error(
                operation='LIST_TRANSACOES_FILTERED',
                error=e,
                entity_type='Transacao',
                error_code='QUERY_ERROR',
                filtros=filtros
            )
            raise TransacaoServiceError(f"Erro ao listar transações: {str(e)}")
    
    @staticmethod
    def excluir_transacao(transacao_id):
        """
        Exclui uma transação específica.
        
        Args:
            transacao_id (int): ID da transação a ser excluída
            
        Raises:
            TransacaoServiceError: Se houver erro na exclusão
        """
        start_time = time.time()
        
        try:
            with transaction.atomic():
                transacao = Transacao.objects.get(id=transacao_id)
                
                # Salvar dados para log antes da exclusão
                conta_id = transacao.conta.id
                conta_nome = transacao.conta.nome
                descricao = transacao.descricao
                valor = float(transacao.valor)
                tipo = transacao.tipo
                
                # Excluir a transação
                transacao.delete()
                
                # Log estruturado de sucesso
                duration_ms = int((time.time() - start_time) * 1000)
                logger.log_operation(
                    level=logging.INFO,
                    operation='DELETE_TRANSACAO',
                    entity_type='Transacao',
                    entity_id=transacao_id,
                    message=f"Transação excluída: {descricao}",
                    duration_ms=duration_ms,
                    conta_id=conta_id,
                    conta_nome=conta_nome,
                    descricao=descricao,
                    valor=valor,
                    tipo=tipo
                )
                
        except Transacao.DoesNotExist:
            logger.log_error(
                operation='DELETE_TRANSACAO',
                error=f"Transação com ID {transacao_id} não encontrada",
                entity_type='Transacao',
                error_code='TRANSACAO_NOT_FOUND',
                entity_id=transacao_id
            )
            raise TransacaoServiceError(ErrorMessages.TRANSACAO_INEXISTENTE)
        except Exception as e:
            logger.log_error(
                operation='DELETE_TRANSACAO',
                error=e,
                entity_type='Transacao',
                error_code='DELETION_ERROR',
                entity_id=transacao_id
            )
            raise TransacaoServiceError(f"Erro ao excluir transação: {str(e)}")