"""Serviços de negócio para a aplicação financas.

Este módulo contém as classes de serviço que centralizam a lógica de negócio,
separando-a das views e models para melhor organização e testabilidade.
"""

from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from .utils import validar_data_futura, get_data_atual_brasil
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
                hoje = get_data_atual_brasil()
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
                    data=data or get_data_atual_brasil(),
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

    @staticmethod
    def gerar_modelo_planilha():
        """
        Gera um modelo de planilha para importação de transações.
        
        Returns:
            bytes: Conteúdo do arquivo Excel em bytes
        """
        import pandas as pd
        import io
        from .constants import TipoTransacao
        from .models import Categoria
        
        try:
            # Criar DataFrame com colunas do modelo
            df = pd.DataFrame(columns=[
                'descricao', 'valor', 'data', 'tipo', 'categoria', 
                'responsavel', 'observacoes', 'conta'
            ])
            
            # Adicionar linha de exemplo
            df.loc[0] = [
                'Exemplo de Transação', '100.00', '2023-01-01', 
                'receita', 'Salário', 'João', 'Observação opcional', 'Conta Principal'
            ]
            
            # Criar buffer para o arquivo Excel
            buffer = io.BytesIO()
            
            # Criar um ExcelWriter
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Transacoes', index=False)
                
                # Obter a planilha para adicionar validações
                workbook = writer.book
                worksheet = writer.sheets['Transacoes']
                
                # Adicionar informações sobre tipos válidos
                tipos_sheet = workbook.create_sheet('Tipos_Validos')
                tipos_sheet['A1'] = 'Tipos de Transação Válidos'
                for i, tipo in enumerate(TipoTransacao.CHOICES):
                    tipos_sheet[f'A{i+2}'] = tipo[0]
                    tipos_sheet[f'B{i+2}'] = tipo[1]
                
                # Adicionar categorias disponíveis
                categorias_sheet = workbook.create_sheet('Categorias')
                categorias_sheet['A1'] = 'Categorias Disponíveis'
                categorias = Categoria.objects.all().values_list('nome', flat=True)
                for i, categoria in enumerate(categorias):
                    categorias_sheet[f'A{i+2}'] = categoria
                
                # Adicionar instruções
                info_sheet = workbook.create_sheet('Instruções')
                info_sheet['A1'] = 'Instruções para Importação de Transações'
                info_sheet['A2'] = '1. Preencha os dados na planilha "Transacoes"'
                info_sheet['A3'] = '2. Formatos de data aceitos: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, MM/DD/YYYY, DD.MM.YYYY'
                info_sheet['A4'] = '3. O valor deve ser um número decimal (ex: 100.00)'
                info_sheet['A5'] = '4. O tipo deve ser "receita" ou "despesa"'
                info_sheet['A6'] = '5. Use categorias existentes ou deixe em branco'
                info_sheet['A7'] = '6. A conta deve existir no sistema'
                info_sheet['A8'] = '7. Responsável e observações são opcionais'
            
            # Retornar o buffer como bytes
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erro ao gerar modelo de planilha: {str(e)}")
            raise TransacaoServiceError(f"Erro ao gerar modelo de planilha: {str(e)}")
    
    @staticmethod
    def importar_transacoes_planilha(arquivo_excel, usuario):
        """
        Importa transações de uma planilha Excel.
        
        Args:
            arquivo_excel: Arquivo Excel enviado pelo usuário
            usuario: Usuário que está realizando a importação
            
        Returns:
            dict: Resultado da importação com estatísticas
            
        Raises:
            TransacaoServiceError: Se houver erro na importação
        """
        import pandas as pd
        from django.db import transaction
        from .models import Categoria, Conta
        from decimal import Decimal, InvalidOperation
        from datetime import datetime
        
        try:
            # Ler o arquivo Excel - forçando o tipo de dados da coluna data como string
            df = pd.read_excel(arquivo_excel, sheet_name='Transacoes', dtype={'data': str})
            
            # Validar colunas obrigatórias
            colunas_obrigatorias = ['descricao', 'valor', 'data', 'tipo']
            for coluna in colunas_obrigatorias:
                if coluna not in df.columns:
                    raise TransacaoServiceError(f"Coluna obrigatória '{coluna}' não encontrada na planilha")
            
            # Estatísticas da importação
            total_linhas = len(df)
            transacoes_importadas = 0
            erros = []
            dados_invalidos = []  # Lista para armazenar dados que precisam de correção manual
            
            # Processar cada linha da planilha em lotes para evitar timeout
            BATCH_SIZE = 50  # Processar 50 transações por vez
            
            # Dividir o dataframe em lotes
            total_rows = len(df)
            for batch_start in range(0, total_rows, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, total_rows)
                batch_df = df.iloc[batch_start:batch_end]
                
                with transaction.atomic():
                    for index, row in batch_df.iterrows():
                    try:
                        # Validar campos obrigatórios
                        if pd.isna(row['descricao']) or pd.isna(row['valor']) or pd.isna(row['data']) or pd.isna(row['tipo']):
                            erros.append(f"Linha {index+2}: Campos obrigatórios não preenchidos")
                            continue
                        
                        # Validar e converter valor
                        try:
                            valor = Decimal(str(row['valor']))
                            if valor <= 0:
                                erros.append(f"Linha {index+2}: Valor deve ser maior que zero")
                                continue
                        except InvalidOperation:
                            erros.append(f"Linha {index+2}: Valor inválido")
                            continue
                        
                        # Validar e converter data - aceitar múltiplos formatos
                        try:
                            # Converter para string para garantir compatibilidade
                            data_str = str(row['data']).strip()
                            # Tentar diferentes formatos de data - priorizando o formato dd/mm/aaaa
                            formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y', 
                                       '%Y/%m/%d', '%Y.%m.%d', '%m/%d/%Y', '%m-%d-%Y', '%m.%d.%Y']
                            data = None
                            for formato in formatos:
                                try:
                                    data = datetime.strptime(data_str, formato).date()
                                    break
                                except ValueError:
                                    continue
                            if data is None:
                                # Adicionar linha e valor aos erros para depuração
                                erros.append(f"Linha {index+2}: Data inválida '{data_str}'. Use o formato DD/MM/AAAA ou AAAA-MM-DD")
                                # Adicionar dados inválidos para correção manual
                                dados_invalidos.append({
                                    'linha': index+2,
                                    'descricao': row.get('descricao', ''),
                                    'valor': row.get('valor', ''),
                                    'data': data_str,  # Manter o valor original para correção
                                    'tipo': row.get('tipo', ''),
                                    'conta': row.get('conta', ''),
                                    'categoria': row.get('categoria', ''),
                                    'responsavel': row.get('responsavel', '')
                                })
                                continue
                        except (ValueError, AttributeError):
                            erros.append(f"Linha {index+2}: Data inválida. Use o formato DD/MM/AAAA ou AAAA-MM-DD")
                            continue
                        
                        # Validar tipo
                        tipo = str(row['tipo']).lower()
                        if not TipoTransacao.is_valid_type(tipo):
                            erros.append(f"Linha {index+2}: Tipo inválido. Use 'receita' ou 'despesa'")
                            continue
                        
                        # Buscar conta (opcional)
                        conta = None
                        if 'conta' in row and not pd.isna(row.get('conta', None)):
                            try:
                                conta = Conta.objects.get(nome=row['conta'])
                            except Conta.DoesNotExist:
                                erros.append(f"Linha {index+2}: Conta '{row['conta']}' não encontrada")
                                continue
                        
                        # Buscar categoria (opcional)
                        categoria = None
                        if 'categoria' in row and not pd.isna(row['categoria']):
                            try:
                                categoria = Categoria.objects.get(nome=row['categoria'])
                            except Categoria.DoesNotExist:
                                erros.append(f"Linha {index+2}: Categoria '{row['categoria']}' não encontrada")
                                continue
                        
                        # Campos opcionais
                        responsavel = None if pd.isna(row.get('responsavel', None)) else str(row['responsavel'])
                        observacoes = None if pd.isna(row.get('observacoes', None)) else str(row['observacoes'])
                        
                        # Criar transação
                        if conta is None:
                            erros.append(f"Linha {index+2}: É necessário informar uma conta válida")
                            continue
                            
                        # Obter tenant_id do usuário
                        from .views import get_tenant_id
                        tenant_id = get_tenant_id(usuario)
                        
                        transacao = Transacao.objects.create(
                            descricao=str(row['descricao']),
                            valor=valor,
                            data=data,
                            tipo=tipo,
                            conta=conta,
                            categoria=categoria,
                            responsavel=responsavel,
                            tenant_id=tenant_id
                        )
                        
                        transacoes_importadas += 1
                        
                    except Exception as e:
                        erros.append(f"Linha {index+2}: {str(e)}")
            
            # Atualizar saldos das contas afetadas - otimizado para evitar timeout
            contas_afetadas = set()
            # Coletar contas afetadas apenas uma vez, fora dos lotes
            for index, row in df.iterrows():
                if 'conta' in row and not pd.isna(row.get('conta', None)):
                    try:
                        conta = Conta.objects.get(nome=row['conta'])
                        contas_afetadas.add(conta.id)
                    except Conta.DoesNotExist:
                        pass
            
            # Atualizar saldos em lotes para evitar timeout
            BATCH_SIZE_SALDOS = 10  # Processar 10 contas por vez
            contas_lista = list(contas_afetadas)
            
            for i in range(0, len(contas_lista), BATCH_SIZE_SALDOS):
                batch_contas = contas_lista[i:i+BATCH_SIZE_SALDOS]
                for conta_id in batch_contas:
                    ContaService.atualizar_saldo_conta(conta_id)
            
            # Verificar se há linhas com erro que ainda não foram adicionadas a dados_invalidos
            # Limitar o número de erros processados para evitar timeout
            MAX_ERROS = 50  # Limitar a 50 erros para não sobrecarregar o sistema
            
            # Se já temos muitos erros, não processar mais
            if len(erros) > MAX_ERROS:
                erros = erros[:MAX_ERROS]
                erros.append(f"Mais de {MAX_ERROS} erros encontrados. Alguns erros foram omitidos.")
            
            # Limitar o número de dados inválidos para evitar sobrecarga de memória
            if len(dados_invalidos) > MAX_ERROS:
                dados_invalidos = dados_invalidos[:MAX_ERROS]
            
            # Verificar apenas um número limitado de linhas com erro
            linhas_verificadas = 0
            for index, row in df.iterrows():
                # Limitar o número de linhas verificadas
                linhas_verificadas += 1
                if linhas_verificadas > 200:  # Verificar apenas as primeiras 200 linhas
                    break
                    
                # Verificar se esta linha teve erro
                linha_com_erro = False
                linha_ja_adicionada = False
                
                # Verificar se a linha tem erro
                for erro in erros:
                    if f"Linha {index+2}:" in erro:
                        linha_com_erro = True
                        break
                
                # Verificar se a linha já foi adicionada aos dados_invalidos
                for dado in dados_invalidos:
                    if dado.get('linha') == index+2:
                        linha_ja_adicionada = True
                        break
                
                # Adicionar apenas se tem erro e ainda não foi adicionada
                if linha_com_erro and not linha_ja_adicionada:
                    dados_invalidos.append({
                        'linha': index+2,
                        'descricao': str(row.get('descricao', '')) if not pd.isna(row.get('descricao', '')) else '',
                        'valor': str(row.get('valor', '')) if not pd.isna(row.get('valor', '')) else '',
                        'data': str(row.get('data', '')) if not pd.isna(row.get('data', '')) else '',
                        'tipo': str(row.get('tipo', '')) if not pd.isna(row.get('tipo', '')) else '',
                        'conta': str(row.get('conta', '')) if not pd.isna(row.get('conta', '')) else '',
                        'categoria': str(row.get('categoria', '')) if not pd.isna(row.get('categoria', '')) else '',
                        'responsavel': str(row.get('responsavel', '')) if not pd.isna(row.get('responsavel', '')) else ''
                    })
            
            resultado = {
                'total_linhas': total_linhas,
                'transacoes_importadas': transacoes_importadas,
                'erros': erros,
                'dados_invalidos': dados_invalidos,
                'sucesso': len(erros) == 0
            }
            
            # Log de sucesso
            logger.info(f"Importação de transações concluída: {transacoes_importadas}/{total_linhas} importadas")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao importar transações: {str(e)}")
            raise TransacaoServiceError(f"Erro ao importar transações: {str(e)}")