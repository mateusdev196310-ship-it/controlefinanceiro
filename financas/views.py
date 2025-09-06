from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
from decimal import Decimal
import calendar
import time
import logging
import re
import uuid

from .models import Categoria, Transacao, Meta, DespesaParcelada, Conta, FechamentoMensal, ConfiguracaoFechamento, CustomUser
from .services import ContaService, TransacaoService
from .constants import TipoTransacao, SuccessMessages, ErrorMessages
from .exceptions import ContaServiceError, TransacaoServiceError
from .logging_config import get_logger
from .utils import parse_currency_value

logger = get_logger(__name__)

def get_tenant_id(user):
    """Obtém o tenant_id do usuário baseado no documento (CPF/CNPJ) ou username."""
    if hasattr(user, 'get_documento') and user.get_documento():
        return hash(user.get_documento()) % 1000000
    return hash(user.username) % 1000000

@login_required
def dashboard(request):
    """
    Dashboard principal com resumo financeiro.
    Utiliza services para centralizar a lógica de negócio.
    """
    try:
        # Obter transações recentes ordenadas por data e horário de criação (mais recentes primeiro)
        # EXCLUINDO despesas parceladas para isolamento completo
        transacoes = Transacao.objects.select_related('categoria').filter(
            despesa_parcelada__isnull=True
        ).order_by('-data', '-id')[:10]
        
        # Data atual para cálculos mensais
        hoje = timezone.now().date()
        
        # Obter resumo financeiro consolidado de todas as contas
        resumos_contas = []
        total_receitas = Decimal('0.00')
        total_despesas = Decimal('0.00')
        saldo_anterior_total = Decimal('0.00')
        saldo_atual_total = Decimal('0.00')
        
        contas = Conta.objects.all()
        
        for conta in contas:
            try:
                resumo = ContaService.obter_resumo_financeiro(
                    conta.id, 
                    mes=hoje.month, 
                    ano=hoje.year
                )
                resumos_contas.append(resumo)
                
                # Somar totais
                total_receitas += resumo['receitas']
                total_despesas += resumo['despesas']
                saldo_anterior_total += resumo['saldo_anterior']
                saldo_atual_total += resumo['saldo_atual']
                
            except ContaServiceError as e:
                logger.error(f"Erro ao obter resumo da conta {conta.nome}: {str(e)}")
                messages.error(request, f"Erro ao carregar dados da conta {conta.nome}")
        
        # Movimentação do mês atual
        movimentacao_mes = total_receitas - total_despesas
    
        # Dados para gráficos de categorias (apenas do mês atual)
        categorias = Categoria.objects.all()
        dados_categorias = []
        
        logger.info(f"Processando {categorias.count()} categorias para o gráfico")
        
        for categoria in categorias:
            # Excluir despesas parceladas dos gráficos de categorias e filtrar por mês atual
            total_categoria = Transacao.objects.filter(
                categoria=categoria, 
                tipo__in=TipoTransacao.get_expense_types(),
                despesa_parcelada__isnull=True,  # Excluir despesas parceladas
                data__month=hoje.month,
                data__year=hoje.year
            ).aggregate(total=Sum('valor'))
            
            logger.info(f"Categoria {categoria.nome}: {total_categoria['total']} (mês {hoje.month}/{hoje.year})")
            
            if total_categoria['total']:
                dados_categorias.append({
                    'nome': categoria.nome,
                    'valor': float(total_categoria['total']),
                    'cor': categoria.cor
                })
        
        logger.info(f"Total de categorias com dados: {len(dados_categorias)}")
        
        # Metas
        metas = Meta.objects.all()
        
        # Nomes dos meses em português
        meses = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        
        mes_atual = meses[hoje.month - 1]
        ano_atual = hoje.year
        
        # Verificar fechamentos do mês atual
        fechamentos_mes_atual = FechamentoMensal.objects.filter(
            mes=hoje.month,
            ano=hoje.year
        ).select_related('conta')
        
        # Preparar informações sobre fechamentos
        info_fechamentos = {
            'tem_fechamentos': fechamentos_mes_atual.exists(),
            'contas_fechadas': list(fechamentos_mes_atual.values_list('conta__nome', flat=True)),
            'total_contas_fechadas': fechamentos_mes_atual.count(),
            'total_contas': contas.count(),
            'eh_mes_atual': True,  # Sempre True no dashboard pois mostra mês atual
        }
        
        # Serializar dados_categorias para JSON
        dados_categorias_json = json.dumps(dados_categorias)
        logger.info(f"Dados categorias JSON: {dados_categorias_json}")
        
        context = {
            'transacoes': transacoes,
            'total_receitas': total_receitas,
            'total_despesas': total_despesas,
            'saldo': saldo_atual_total,
            'saldo_anterior': saldo_anterior_total,
            'movimentacao_mes': movimentacao_mes,
            'mes_atual': mes_atual,
            'ano_atual': ano_atual,
            'dados_categorias': dados_categorias,
            'dados_categorias_json': dados_categorias_json,
            'metas': metas,
            'contas': contas,
            'resumos_contas': resumos_contas,
            'info_fechamentos': info_fechamentos,
        }
        
        logger.info(f"Dashboard carregado com sucesso - {len(contas)} contas processadas")
        return render(request, 'financas/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Erro inesperado no dashboard: {str(e)}")
        messages.error(request, "Erro ao carregar o dashboard. Tente novamente.")
        
        # Contexto mínimo em caso de erro
        context = {
            'transacoes': [],
            'total_receitas': 0,
            'total_despesas': 0,
            'saldo': 0,
            'saldo_anterior': 0,
            'movimentacao_mes': 0,
            'mes_atual': 'N/A',
            'ano_atual': timezone.now().year,
            'dados_categorias': [],
            'metas': [],
            'contas': [],
        }
        
        return render(request, 'financas/dashboard.html', context)

@login_required
def transacoes(request):
    """
    Lista transações com filtros usando TransacaoService.
    Inclui paginação, totalizadores e filtro padrão dos últimos 30 dias.
    """
    try:
        # Extrair filtros da query string
        filtros = {
            'data_inicio': request.GET.get('data_inicio'),
            'data_fim': request.GET.get('data_fim'),
            'categoria_id': request.GET.get('categoria'),
            'tipo': request.GET.get('tipo'),
            'responsavel': request.GET.get('responsavel'),
            'descricao': request.GET.get('descricao'),
        }
        
        # Se não há filtros de data, aplicar filtro padrão dos últimos 30 dias
        if not filtros['data_inicio'] and not filtros['data_fim'] and not any(request.GET.values()):
            data_fim = timezone.now().date()
            data_inicio = data_fim - timedelta(days=30)
            filtros['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
            filtros['data_fim'] = data_fim.strftime('%Y-%m-%d')
        
        # Remover filtros vazios
        filtros = {k: v for k, v in filtros.items() if v}
        
        # Obter transações usando o service
        transacoes = TransacaoService.listar_transacoes_com_filtros(**filtros)
        
        # Calcular totalizadores para as transações filtradas
        totalizadores = TransacaoService.calcular_totalizadores(transacoes)
        
        # Paginação
        paginator = Paginator(transacoes, 20)  # 20 transações por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Obter categorias para o formulário de filtro
        categorias = Categoria.objects.all().order_by('nome')
        
        context = {
            'page_obj': page_obj,
            'transacoes': page_obj,  # Para compatibilidade com templates existentes
            'categorias': categorias,
            'filtros_aplicados': filtros,
            'tipos_transacao': TipoTransacao.CHOICES,
            'totalizadores': totalizadores,
        }
        
        logger.info(f"Lista de transações carregada - {transacoes.count()} transações encontradas")
        return render(request, 'financas/transacoes.html', context)
        
    except TransacaoServiceError as e:
        logger.error(f"Erro do serviço ao listar transações: {str(e)}")
        messages.error(request, str(e))
        
        # Contexto mínimo em caso de erro
        context = {
            'page_obj': None,
            'transacoes': [],
            'categorias': [],
            'filtros_aplicados': {},
            'tipos_transacao': TipoTransacao.CHOICES,
        }
        return render(request, 'financas/transacoes.html', context)
        
    except Exception as e:
        logger.error(f"Erro inesperado ao listar transações: {str(e)}")
        messages.error(request, "Erro ao carregar as transações. Tente novamente.")
        
        # Contexto mínimo em caso de erro
        context = {
            'page_obj': None,
            'transacoes': [],
            'categorias': [],
            'filtros_aplicados': {},
            'tipos_transacao': TipoTransacao.CHOICES,
        }
        return render(request, 'financas/transacoes.html', context)

def adicionar_transacao(request, transacao_id=None):
    """
    Adiciona uma nova transação ou edita uma existente usando o TransacaoService.
    Inclui validações e tratamento de erros robusto.
    """
    # Verificar se é edição
    transacao_existente = None
    if transacao_id:
        transacao_existente = get_object_or_404(Transacao.objects, id=transacao_id)
    
    if request.method == 'POST':
        try:
            # Debug: Log dos dados recebidos
            logger.info(f"POST data recebido: {dict(request.POST)}")
            
            # Extrair dados do formulário
            descricao = request.POST.get('descricao', '').strip()
            valor_str = request.POST.get('valor', '')
            categoria_id = request.POST.get('categoria')
            conta_id = request.POST.get('conta')
            tipo = request.POST.get('tipo')
            data_str = request.POST.get('data')
            responsavel = request.POST.get('responsavel', '').strip()
            
            # Debug: Log dos dados extraídos
            logger.info(f"Dados extraídos - descricao: {descricao}, valor: {valor_str}, categoria_id: {categoria_id}, conta_id: {conta_id}, tipo: {tipo}, data: {data_str}")
            
            # Validações básicas removidas para permitir lançamento livre
            # campos_obrigatorios = [descricao, valor_str, categoria_id, conta_id, tipo]
            # if not all(campos_obrigatorios):
            #     logger.warning(f"Validação falhou - campos obrigatórios vazios: descricao={bool(descricao)}, valor={bool(valor_str)}, categoria={bool(categoria_id)}, conta={bool(conta_id)}, tipo={bool(tipo)}")
            #     messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
            #     return redirect('adicionar_transacao')
            
            logger.info("Validação básica passou - todos os campos obrigatórios preenchidos")
            
            # Converter valor para Decimal usando função utilitária
            try:
                valor = parse_currency_value(valor_str)
                logger.info(f"Valor convertido: {valor_str} -> {valor}")
            except (ValueError, TypeError) as e:
                logger.error(f"Erro ao converter valor '{valor_str}': {e}")
                messages.error(request, "Valor inválido. Use apenas números.")
                return redirect('transacao_create')
            
            # Converter data se fornecida
            data = None
            if data_str:
                try:
                    data = datetime.strptime(data_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, "Data inválida. Use o formato DD/MM/AAAA.")
                    return redirect('transacao_create')
            
            # Verificar se categoria existe
            categoria = get_object_or_404(Categoria.objects, id=categoria_id)
            logger.info(f"Categoria encontrada: {categoria.nome} (tipo: {categoria.tipo})")
            
            # Validação de compatibilidade removida para permitir lançamento livre
            # if categoria.tipo != 'ambos' and categoria.tipo != tipo:
            #     error_msg = f"A categoria '{categoria.nome}' é do tipo '{categoria.tipo}' e não pode ser usada para transações do tipo '{tipo}'."
            #     logger.warning(f"Validação de tipo falhou - categoria: {categoria.tipo}, transação: {tipo}")
            #     messages.error(request, error_msg)
            #     return redirect('adicionar_transacao')
            
            if transacao_existente:
                # Atualizar transação existente
                logger.info(f"Atualizando transação ID={transacao_id}")
                
                # Verificar se o mês da transação original não está fechado
                from .utils import verificar_mes_fechado
                mes_fechado_original, _ = verificar_mes_fechado(transacao_existente.data, transacao_existente.conta)
                if mes_fechado_original:
                    messages.error(request, f"Não é possível editar transação de {transacao_existente.data.strftime('%m/%Y')} pois o mês já foi fechado.")
                    return redirect('transacoes')
                
                # Se a data foi alterada, verificar se o novo mês também não está fechado
                if data and data != transacao_existente.data:
                    mes_fechado_novo, _ = verificar_mes_fechado(data, transacao_existente.conta)
                    if mes_fechado_novo:
                        messages.error(request, f"Não é possível alterar data para {data.strftime('%m/%Y')} pois o mês já foi fechado.")
                        return redirect('transacoes')
                
                transacao_existente.descricao = descricao
                transacao_existente.valor = valor
                transacao_existente.categoria = categoria
                transacao_existente.conta_id = int(conta_id)
                transacao_existente.tipo = tipo
                transacao_existente.responsavel = responsavel
                if data:
                    transacao_existente.data = data
                
                transacao_existente.save()
                transacao = transacao_existente
                
                logger.info(f"Transação atualizada com sucesso: ID={transacao.id}, descricao={transacao.descricao}")
                messages.success(request, SuccessMessages.TRANSACAO_ATUALIZADA)
            else:
                # Criar nova transação usando o service
                logger.info(f"Chamando TransacaoService.criar_transacao com: conta_id={conta_id}, descricao={descricao}, valor={valor}, tipo={tipo}, data={data}, categoria={categoria.nome}")
                
                transacao = TransacaoService.criar_transacao(
                    conta_id=int(conta_id),
                    descricao=descricao,
                    valor=valor,
                    tipo=tipo,
                    data=data,
                    categoria=categoria.nome  # Passar nome da categoria
                )
                
                logger.info(f"Transação criada com sucesso: ID={transacao.id}, descricao={transacao.descricao}")
                messages.success(request, SuccessMessages.TRANSACAO_CRIADA)
            logger.info(
                f"Transação criada com sucesso: {transacao.descricao} - "
                f"R$ {transacao.valor} ({transacao.tipo})"
            )
            
            return redirect('transacoes')
            
        except TransacaoServiceError as e:
            logger.error(f"Erro do serviço ao criar transação: {str(e)}")
            messages.error(request, str(e))
            return redirect('adicionar_transacao')
            
        except Exception as e:
            logger.error(f"Erro inesperado ao criar transação: {str(e)}")
            messages.error(request, "Erro interno. Tente novamente.")
            return redirect('transacao_create')
    
    # GET request - mostrar formulário
    try:
        categorias = Categoria.objects.all()
        contas = Conta.objects.all()
        
        context = {
            'categorias': categorias,
            'contas': contas,
            'tipos_transacao': TipoTransacao.CHOICES,
            'transacao': transacao_existente,
            'is_edit': bool(transacao_existente)
        }
        
        return render(request, 'financas/adicionar_transacao.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao carregar formulário de transação: {str(e)}")
        messages.error(request, "Erro ao carregar o formulário.")
        return redirect('dashboard')

@login_required
def adicionar_categoria(request):
    """
    View para adicionar nova categoria com validação robusta.
    
    Valida:
    - Nome não vazio e com tamanho adequado
    - Unicidade do nome da categoria
    - Cor padrão se não fornecida
    
    Redireciona para 'transacoes' em caso de sucesso,
    ou para 'adicionar_categoria' em caso de erro.
    Suporta requisições AJAX retornando JSON.
    """
    if request.method == 'POST':
        start_time = time.time()
        nome = request.POST.get('nome', '').strip()
        tipo = request.POST.get('tipo', 'ambos').strip()
        cor = request.POST.get('cor', '#007bff').strip()  # Cor padrão azul
        
        # Validação do nome
        if not nome:
            error_msg = ErrorMessages.CATEGORIA_NOME_OBRIGATORIO
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            logger.log_validation_error(
                operation='CREATE_CATEGORIA',
                field='nome',
                value='',
                error='Nome obrigatório'
            )
            return render(request, 'financas/adicionar_categoria.html')
        
        if len(nome) < 2:
            error_msg = "Nome da categoria deve ter pelo menos 2 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            logger.log_validation_error(
                operation='CREATE_CATEGORIA',
                field='nome',
                value=nome,
                error='Nome muito curto (< 2 caracteres)'
            )
            return render(request, 'financas/adicionar_categoria.html')
        
        if len(nome) > 50:
            error_msg = "Nome da categoria deve ter no máximo 50 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            logger.log_validation_error(
                operation='CREATE_CATEGORIA',
                field='nome',
                value=f"{nome[:20]}...",
                error='Nome muito longo (> 50 caracteres)'
            )
            return render(request, 'financas/adicionar_categoria.html')
        
        # Verificar unicidade
        if Categoria.objects.filter(nome__iexact=nome).exists():
            error_msg = f"Já existe uma categoria com o nome '{nome}'"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            logger.log_validation_error(
                operation='CREATE_CATEGORIA',
                field='nome',
                value=nome,
                error='Nome duplicado'
            )
            return render(request, 'financas/adicionar_categoria.html')
        
        # Validação da cor (formato hexadecimal)
        if not cor.startswith('#') or len(cor) != 7:
            cor = '#007bff'  # Cor padrão se inválida
            logger.log_operation(
                 level=logging.INFO,
                 operation='CREATE_CATEGORIA',
                 message=f"Cor inválida fornecida, usando cor padrão: {cor}",
                 entity_type='Categoria'
             )
        
        try:
            # Criar categoria
            categoria = Categoria.objects.create(
                nome=nome,
                tipo=tipo,
                cor=cor
            )
            
            # Log estruturado de sucesso
            duration_ms = int((time.time() - start_time) * 1000)
            logger.log_operation(
                 level=logging.INFO,
                 operation='CREATE_CATEGORIA',
                 entity_type='Categoria',
                 entity_id=categoria.id,
                 message=f"Categoria criada com sucesso: {categoria.nome}",
                 duration_ms=duration_ms,
                 nome=categoria.nome,
                 cor=categoria.cor
             )
            
            # Retorno para AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'categoria': {
                        'id': categoria.id,
                        'nome': categoria.nome,
                        'tipo': categoria.tipo,
                        'cor': categoria.cor
                    }
                })
            
            messages.success(request, f"Categoria '{categoria.nome}' criada com sucesso!")
            return redirect('categorias')
            
        except Exception as e:
            logger.log_error(
                operation='CREATE_CATEGORIA',
                error=e,
                entity_type='Categoria',
                error_code='CREATION_ERROR',
                nome=nome,
                cor=cor
            )
            error_msg = f"Erro ao criar categoria: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return render(request, 'financas/adicionar_categoria.html')
    
    return render(request, 'financas/adicionar_categoria.html')

@login_required
def categorias(request):
    """
    View para listar todas as categorias com opção de adicionar nova.
    """
    categorias = Categoria.objects.all().order_by('nome')
    
    context = {
        'categorias': categorias,
        'total_categorias': categorias.count(),
    }
    
    return render(request, 'financas/categorias.html', context)

def editar_categoria(request, categoria_id):
    """
    View para editar uma categoria existente.
    """
    categoria = get_object_or_404(Categoria.objects, id=categoria_id)
    
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        tipo = request.POST.get('tipo', 'ambos').strip()
        cor = request.POST.get('cor', '#007bff').strip()
        
        # Validação do nome
        if not nome:
            messages.error(request, 'Nome da categoria é obrigatório.')
            return render(request, 'financas/editar_categoria.html', {'categoria': categoria})
        
        if len(nome) < 2:
            messages.error(request, 'Nome da categoria deve ter pelo menos 2 caracteres.')
            return render(request, 'financas/editar_categoria.html', {'categoria': categoria})
        
        if len(nome) > 50:
            messages.error(request, 'Nome da categoria deve ter no máximo 50 caracteres.')
            return render(request, 'financas/editar_categoria.html', {'categoria': categoria})
        
        # Verificar unicidade (excluindo a própria categoria)
        if Categoria.objects.filter(nome__iexact=nome).exclude(id=categoria_id).exists():
            messages.error(request, f"Já existe uma categoria com o nome '{nome}'")
            return render(request, 'financas/editar_categoria.html', {'categoria': categoria})
        
        # Validação da cor
        if not cor.startswith('#') or len(cor) != 7:
            cor = '#007bff'
        
        try:
            categoria.nome = nome
            categoria.tipo = tipo
            categoria.cor = cor
            categoria.save()
            
            messages.success(request, f"Categoria '{categoria.nome}' atualizada com sucesso!")
            return redirect('categorias')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar categoria: {str(e)}')
            return render(request, 'financas/editar_categoria.html', {'categoria': categoria})
    
    return render(request, 'financas/editar_categoria.html', {'categoria': categoria})

def excluir_categoria(request, categoria_id):
    """
    View para excluir uma categoria.
    """
    categoria = get_object_or_404(Categoria.objects, id=categoria_id)
    
    # Verificar se a categoria está sendo usada em transações
    transacoes_count = Transacao.objects.filter(categoria=categoria).count()
    
    if transacoes_count > 0:
        messages.error(request, f'Não é possível excluir a categoria "{categoria.nome}" pois ela está sendo usada em {transacoes_count} transação(ões).')
        return redirect('categorias')
    
    try:
        nome_categoria = categoria.nome
        categoria.delete()
        messages.success(request, f'Categoria "{nome_categoria}" excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir categoria: {str(e)}')
    
    return redirect('categorias')

@login_required
def adicionar_despesa_parcelada(request):
    if request.method == 'POST':
        descricao = request.POST.get('descricao')
        valor_total = request.POST.get('valor_total')
        categoria_id = request.POST.get('categoria')
        conta_id = request.POST.get('conta')
        responsavel = request.POST.get('responsavel')
        total_parcelas = request.POST.get('total_parcelas')
        data_primeira_parcela = request.POST.get('data_primeira_parcela')
        intervalo = request.POST.get('intervalo')
        
        # Debug: Log dos valores recebidos
        logger.info(f"DEBUG - Valores recebidos do formulário:")
        logger.info(f"  descricao: '{descricao}'")
        logger.info(f"  valor_total: '{valor_total}'")
        logger.info(f"  categoria_id: '{categoria_id}'")
        logger.info(f"  conta_id: '{conta_id}'")
        logger.info(f"  total_parcelas: '{total_parcelas}'")
        logger.info(f"  data_primeira_parcela: '{data_primeira_parcela}'")
        logger.info(f"  intervalo: '{intervalo}'")
        
        if all([descricao, valor_total, categoria_id, conta_id, total_parcelas, data_primeira_parcela, intervalo]):
            try:
                categoria = Categoria.objects.get(id=categoria_id)
                conta = Conta.objects.get(id=conta_id)
                # Converter valor total usando função utilitária
                valor_total_decimal = parse_currency_value(valor_total)
                logger.info(f"DEBUG - Valor convertido: {valor_total_decimal}")
                
                despesa_parcelada = DespesaParcelada.objects.create(
                    descricao=descricao,
                    valor_total=valor_total_decimal,
                    categoria=categoria,
                    conta=conta,
                    responsavel=responsavel or '',
                    numero_parcelas=int(total_parcelas),
                    data_primeira_parcela=datetime.strptime(data_primeira_parcela, '%Y-%m-%d').date(),
                    intervalo_tipo=intervalo
                )
                logger.info(f"DEBUG - DespesaParcelada criada: ID={despesa_parcelada.id}, valor_total={despesa_parcelada.valor_total}")
                despesa_parcelada.gerar_parcelas()
                logger.info(f"DEBUG - Parcelas geradas para despesa {despesa_parcelada.id}")
                messages.success(request, f'Despesa parcelada criada com sucesso! {total_parcelas} parcelas foram geradas.')
                # Redirecionar para detalhes com parâmetro indicando parcelas recém-geradas
                from django.http import HttpResponseRedirect
                from django.urls import reverse
                url = reverse('detalhes_despesa_parcelada', args=[despesa_parcelada.id]) + '?parcelas_geradas=true'
                return HttpResponseRedirect(url)
            except Exception as e:
                logger.error(f"DEBUG - Erro ao criar despesa parcelada: {str(e)}")
                messages.error(request, f'Erro ao criar despesa parcelada: {str(e)}')
        else:
            logger.warning(f"DEBUG - Campos obrigatórios faltando. Valores: descricao={descricao}, valor_total={valor_total}, categoria_id={categoria_id}, conta_id={conta_id}, total_parcelas={total_parcelas}, data_primeira_parcela={data_primeira_parcela}, intervalo={intervalo}")
    
    categorias = Categoria.objects.all()
    contas = Conta.objects.all()
    context = {
        'categorias': categorias,
        'contas': contas,
    }
    return render(request, 'financas/adicionar_despesa_parcelada.html', context)

@login_required
def despesas_parceladas(request):
    from decimal import Decimal
    from django.db.models import Sum
    
    despesas = DespesaParcelada.objects.all().order_by('-criada_em')
    
    # Calcular totalizadores
    total_despesas = despesas.count()
    valor_total_geral = despesas.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
    total_parcelas = sum(despesa.numero_parcelas for despesa in despesas)
    
    # Calcular valores pagos e pendentes
    valor_total_pago = Decimal('0.00')
    valor_total_pendente = Decimal('0.00')
    despesas_ativas = 0
    
    for despesa in despesas:
        valor_pago = despesa.get_valor_pago()
        valor_pendente = despesa.get_valor_pendente()
        valor_total_pago += valor_pago
        valor_total_pendente += valor_pendente
        
        # Considera ativa se tem parcelas pendentes
        if valor_pendente > 0:
            despesas_ativas += 1
    
    context = {
        'despesas': despesas,
        'total_despesas': total_despesas,
        'valor_total_geral': valor_total_geral,
        'total_parcelas': total_parcelas,
        'despesas_ativas': despesas_ativas,
        'valor_total_pago': valor_total_pago,
        'valor_total_pendente': valor_total_pendente,
    }
    return render(request, 'financas/despesas_parceladas.html', context)

@login_required
def detalhes_despesa_parcelada(request, despesa_id):
    from datetime import date
    despesa = get_object_or_404(DespesaParcelada.objects, id=despesa_id)
    parcelas = despesa.get_parcelas()
    
    # Verificar se as parcelas foram recém-geradas
    parcelas_recem_geradas = request.GET.get('parcelas_geradas') == 'true'
    
    context = {
        'despesa': despesa,
        'parcelas': parcelas,
        'today': date.today(),
        'parcelas_recem_geradas': parcelas_recem_geradas,
    }
    return render(request, 'financas/detalhes_despesa_parcelada.html', context)

@login_required
def criar_conta(request):
    """View para criar uma nova conta"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        saldo_inicial = request.POST.get('saldo_inicial') or request.POST.get('saldo', 0)
        tipo = request.POST.get('tipo', 'simples')
        
        # Validar se nome foi fornecido
        if not nome or not nome.strip():
            messages.error(request, 'Nome da conta é obrigatório.')
            from .models import Banco
            bancos = Banco.objects.all().order_by('codigo')
            return render(request, 'financas/criar_conta.html', {'bancos': bancos})
        
        # Criar a conta com saldo zero
        conta = Conta.objects.create(
            nome=nome.strip(),
            saldo=0,
            tipo=tipo
        )
        
        # Se for conta bancária, adicionar informações do banco
        if tipo == 'bancaria':
            banco_id = request.POST.get('banco')
            if banco_id:
                from .models import Banco
                conta.banco_id = banco_id
            conta.cnpj = request.POST.get('cnpj', '')
            conta.numero_conta = request.POST.get('numero_conta', '')
            conta.agencia = request.POST.get('agencia', '')
            conta.save()
        
        # Se há saldo inicial, criar uma transação de receita no mês atual
        if saldo_inicial and float(saldo_inicial) > 0:
            # Buscar ou criar categoria "Saldo Inicial"
            categoria_saldo, created = Categoria.objects.get_or_create(
                nome='Saldo Inicial',
                defaults={'cor': '#28a745'}  # Verde
            )
            
            # Criar transação de receita
            Transacao.objects.create(
                descricao=f'Saldo inicial da conta {nome}',
                valor=saldo_inicial,
                categoria=categoria_saldo,
                tipo='receita',
                data=timezone.now().date(),
                responsavel='Sistema',
                conta=conta
            )
            
            # Atualizar saldo da conta
            conta.saldo = saldo_inicial
            conta.save()
        
        messages.success(request, 'Conta criada com sucesso!')
        return redirect('contas')
    
    # GET request - mostrar formulário
    from .models import Banco
    bancos = Banco.objects.all().order_by('codigo')
    return render(request, 'financas/criar_conta.html', {'bancos': bancos})

@login_required
def contas(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        saldo_inicial = request.POST.get('saldo_inicial') or request.POST.get('saldo', 0)
        tipo = request.POST.get('tipo', 'simples')
        
        # Validar se nome foi fornecido
        if not nome or not nome.strip():
            messages.error(request, 'Nome da conta é obrigatório.')
            from .models import Banco
            contas = Conta.objects.all()
            bancos = Banco.objects.all().order_by('codigo')
            
            context = {
                'contas': contas,
                'bancos': bancos,
            }
            return render(request, 'financas/contas.html', context)
        
        # Criar a conta com saldo zero
        conta = Conta.objects.create(
            nome=nome.strip(),
            saldo=0,
            tipo=tipo
        )
        
        # Se for conta bancária, adicionar informações do banco
        if tipo == 'bancaria':
            banco_id = request.POST.get('banco')
            if banco_id:
                from .models import Banco
                conta.banco_id = banco_id
            conta.cnpj = request.POST.get('cnpj', '')
            conta.numero_conta = request.POST.get('numero_conta', '')
            conta.agencia = request.POST.get('agencia', '')
            conta.save()
        
        # Se há saldo inicial, criar uma transação de receita no mês atual
        if saldo_inicial and float(saldo_inicial) > 0:
            # Buscar ou criar categoria "Saldo Inicial"
            categoria_saldo, created = Categoria.objects.get_or_create(
                nome='Saldo Inicial',
                defaults={'cor': '#28a745'}  # Verde
            )
            
            # Criar transação de receita
            Transacao.objects.create(
                descricao=f'Saldo inicial da conta {nome}',
                valor=saldo_inicial,
                categoria=categoria_saldo,
                tipo='receita',
                data=timezone.now().date(),
                responsavel='Sistema',
                conta=conta
            )
            
            # Atualizar saldo da conta
            conta.saldo = saldo_inicial
            conta.save()
        
        messages.success(request, 'Conta criada com sucesso!')
        return redirect('contas')
    
    from .models import Banco
    contas = Conta.objects.all()
    bancos = Banco.objects.all().order_by('codigo')
    
    context = {
        'contas': contas,
        'bancos': bancos,
    }
    return render(request, 'financas/contas.html', context)

def editar_conta(request, conta_id):
    from .models import Banco
    conta = get_object_or_404(Conta.objects, id=conta_id)
    bancos = Banco.objects.all()
    
    if request.method == 'POST':
        conta.nome = request.POST.get('nome')
        conta.tipo = request.POST.get('tipo', 'simples')
        
        # Atualizar saldo se fornecido
        novo_saldo = request.POST.get('saldo')
        if novo_saldo:
            try:
                novo_saldo_decimal = Decimal(novo_saldo)
                diferenca = novo_saldo_decimal - conta.saldo
                conta.saldo = novo_saldo_decimal
                
                # Criar transação para registrar a alteração de saldo
                if diferenca != 0:
                    from .models import Transacao
                    Transacao.objects.create(
                        conta=conta,
                        tipo='receita' if diferenca > 0 else 'despesa',
                        valor=abs(diferenca),
                        descricao=f'Ajuste de saldo da conta {conta.nome}',
                        categoria='Ajuste de Saldo'
                    )
            except (ValueError, TypeError):
                pass  # Ignorar valores inválidos
        
        # Se for conta bancária, salvar dados bancários
        if conta.tipo == 'bancaria':
            banco_id = request.POST.get('banco')
            if banco_id:
                conta.banco_id = banco_id
            conta.cnpj = request.POST.get('cnpj')
            conta.agencia = request.POST.get('agencia')
            conta.numero_conta = request.POST.get('numero_conta')
        else:
            # Se mudou para conta simples, limpar dados bancários
            conta.banco = None
            conta.cnpj = ''
            conta.agencia = ''
            conta.numero_conta = ''
        
        conta.save()
        messages.success(request, 'Conta atualizada com sucesso!')
        return redirect('contas')
    
    context = {
        'conta': conta,
        'bancos': bancos,
    }
    return render(request, 'financas/editar_conta.html', context)

def excluir_conta(request, conta_id):
    conta = get_object_or_404(Conta.objects, id=conta_id)
    
    if request.method == 'POST':
        nome_conta = conta.nome
        conta.delete()
        messages.success(request, f'Conta "{nome_conta}" excluída com sucesso!')
        return redirect('dashboard')
    
    context = {
        'conta': conta,
    }
    return render(request, 'financas/confirmar_exclusao_conta.html', context)

@login_required
def excluir_conta_segura(request, conta_id):
    conta = get_object_or_404(Conta.objects, id=conta_id)
    
    # Verificações de segurança
    saldo_atual = conta.saldo
    tem_transacoes = Transacao.objects.filter(conta=conta).exists()
    tem_parcelas = DespesaParcelada.objects.filter(conta=conta).exists()
    
    # Bloquear exclusão se houver dados importantes
    pode_excluir = True
    motivos_bloqueio = []
    
    if saldo_atual != 0:
        pode_excluir = False
        motivos_bloqueio.append(f'A conta possui saldo de R$ {saldo_atual:.2f}')
    
    if tem_transacoes:
        pode_excluir = False
        qtd_transacoes = Transacao.objects.filter(conta=conta).count()
        motivos_bloqueio.append(f'A conta possui {qtd_transacoes} transação(ões) associada(s)')
    
    if tem_parcelas:
        pode_excluir = False
        qtd_parcelas = DespesaParcelada.objects.filter(conta=conta).count()
        motivos_bloqueio.append(f'A conta possui {qtd_parcelas} despesa(s) parcelada(s) associada(s)')
    
    if request.method == 'POST':
        if pode_excluir:
            confirmacao = request.POST.get('confirmacao_dupla')
            if confirmacao == 'CONFIRMO A EXCLUSAO':
                nome_conta = conta.nome
                conta.delete()
                messages.success(request, f'Conta "{nome_conta}" excluída com sucesso!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Confirmação inválida. Digite exatamente "CONFIRMO A EXCLUSAO" para confirmar.')
        else:
            messages.error(request, 'Não é possível excluir esta conta pelos motivos listados.')
    
    context = {
        'conta': conta,
        'pode_excluir': pode_excluir,
        'motivos_bloqueio': motivos_bloqueio,
        'saldo_atual': saldo_atual,
        'tem_transacoes': tem_transacoes,
        'tem_parcelas': tem_parcelas,
    }
    return render(request, 'financas/confirmar_exclusao_conta_segura.html', context)

@login_required
def transferir_dados_conta(request, conta_origem_id):
    conta_origem = get_object_or_404(Conta.objects, id=conta_origem_id)
    contas_destino = Conta.objects.exclude(id=conta_origem_id)
    
    if not contas_destino.exists():
        messages.error(request, 'É necessário ter pelo menos uma outra conta para transferir os dados.')
        return redirect('contas')
    
    if request.method == 'POST':
        conta_destino_id = request.POST.get('conta_destino')
        conta_destino = get_object_or_404(Conta.objects, id=conta_destino_id)
        
        try:
            # Transferir transações
            transacoes = Transacao.objects.filter(conta=conta_origem)
            qtd_transacoes = transacoes.count()
            transacoes.update(conta=conta_destino)
            
            # Transferir despesas parceladas
            despesas = DespesaParcelada.objects.filter(conta=conta_origem)
            qtd_despesas = despesas.count()
            despesas.update(conta=conta_destino)
            
            # Atualizar saldos
            conta_destino.atualizar_saldo()
            
            # Excluir conta origem
            nome_conta_origem = conta_origem.nome
            nome_conta_destino = conta_destino.nome
            conta_origem.delete()
            
            messages.success(request, 
                f'Dados transferidos com sucesso! {qtd_transacoes} transação(ões) e {qtd_despesas} despesa(s) parcelada(s) '
                f'foram movidas de "{nome_conta_origem}" para "{nome_conta_destino}".')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Erro ao transferir dados: {str(e)}')
    
    context = {
        'conta_origem': conta_origem,
        'contas_destino': contas_destino,
        'qtd_transacoes': Transacao.objects.filter(conta=conta_origem).count(),
        'qtd_despesas': DespesaParcelada.objects.filter(conta=conta_origem).count(),
    }
    return render(request, 'financas/transferir_dados_conta.html', context)

@login_required
def relatorios(request):
    from datetime import datetime, timedelta
    from django.db.models import Q
    
    # Obter parâmetros dos filtros
    periodo = request.GET.get('periodo', 'mes_atual')
    tipo_exibicao = request.GET.get('tipo_exibicao', 'mensal')
    data_inicio_param = request.GET.get('data_inicio')
    data_fim_param = request.GET.get('data_fim')
    
    # Definir datas baseadas no período selecionado
    hoje = datetime.now().date()
    
    if periodo == 'hoje':
        data_inicio = hoje
        data_fim = hoje
    elif periodo == 'semana_atual':
        # Início da semana (segunda-feira)
        data_inicio = hoje - timedelta(days=hoje.weekday())
        data_fim = data_inicio + timedelta(days=6)
    elif periodo == 'ultimos_30_dias':
        data_inicio = hoje - timedelta(days=30)
        data_fim = hoje
    elif periodo == 'personalizado' and data_inicio_param and data_fim_param:
        data_inicio = datetime.strptime(data_inicio_param, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_param, '%Y-%m-%d').date()
    else:  # mes_atual (padrão)
        data_inicio = hoje.replace(day=1)
        # Data atual (não incluir datas futuras)
        data_fim = hoje
    
    # Filtrar transações pelo período
    filtro_periodo = Q(data__gte=data_inicio, data__lte=data_fim)
    
    # Dados para relatórios baseados no período filtrado
    receitas = Transacao.objects.filter(tipo='receita').filter(filtro_periodo).aggregate(total=Sum('valor'))
    despesas = Transacao.objects.filter(tipo__in=['despesa', 'saida']).filter(filtro_periodo).aggregate(total=Sum('valor'))
    
    total_receitas = receitas['total'] if receitas['total'] else 0
    total_despesas = despesas['total'] if despesas['total'] else 0
    saldo = total_receitas - total_despesas
    
    # Dados por categoria para gráfico (filtrado pelo período)
    categorias = Categoria.objects.all()
    dados_categorias = []
    
    for categoria in categorias:
        total_categoria = Transacao.objects.filter(categoria=categoria, tipo='despesa').filter(filtro_periodo).aggregate(total=Sum('valor'))
        if total_categoria['total']:
            dados_categorias.append({
                'nome': categoria.nome,
                'cor': categoria.cor,
                'valor': float(total_categoria['total']),
                'percentual': round((float(total_categoria['total']) / float(total_despesas)) * 100, 1) if total_despesas > 0 else 0
            })
    
    # Ordenar categorias do maior para menor valor
    dados_categorias.sort(key=lambda x: x['valor'], reverse=True)
    
    # Dados de evolução do saldo baseado no tipo de exibição
    dados_evolucao = []
    
    if tipo_exibicao == 'diario':
        # Evolução diária no período selecionado
        saldo_acumulado = 0
        data_atual = data_inicio
        
        while data_atual <= data_fim:
            # Calcular receitas e despesas do dia
            receitas_dia = Transacao.objects.filter(
                tipo='receita',
                data=data_atual
            ).aggregate(total=Sum('valor'))['total'] or 0
            
            despesas_dia = Transacao.objects.filter(
                tipo='despesa',
                data=data_atual
            ).aggregate(total=Sum('valor'))['total'] or 0
            
            saldo_acumulado += float(receitas_dia) - float(despesas_dia)
            
            dados_evolucao.append({
                'data': data_atual.strftime('%d/%m'),
                'saldo': saldo_acumulado
            })
            
            data_atual += timedelta(days=1)
            
    elif tipo_exibicao == 'semanal':
        # Evolução semanal no período selecionado
        saldo_acumulado = 0
        data_atual = data_inicio
        
        while data_atual <= data_fim:
            # Início e fim da semana
            inicio_semana = data_atual - timedelta(days=data_atual.weekday())
            fim_semana = inicio_semana + timedelta(days=6)
            
            # Ajustar para não ultrapassar o período
            if fim_semana > data_fim:
                fim_semana = data_fim
            
            # Calcular receitas e despesas da semana
            receitas_semana = Transacao.objects.filter(
                tipo='receita',
                data__gte=inicio_semana,
                data__lte=fim_semana
            ).aggregate(total=Sum('valor'))['total'] or 0
            
            despesas_semana = Transacao.objects.filter(
                tipo='despesa',
                data__gte=inicio_semana,
                data__lte=fim_semana
            ).aggregate(total=Sum('valor'))['total'] or 0
            
            saldo_acumulado += float(receitas_semana) - float(despesas_semana)
            
            dados_evolucao.append({
                'data': f"{inicio_semana.strftime('%d/%m')} - {fim_semana.strftime('%d/%m')}",
                'saldo': saldo_acumulado
            })
            
            data_atual = fim_semana + timedelta(days=1)
            
    else:  # mensal (padrão)
        # Tentar usar fechamentos mensais primeiro
        fechamentos = FechamentoMensal.objects.filter(fechado=True).order_by('ano', 'mes')[:12]
        
        if fechamentos.exists() and periodo in ['mes_atual', 'ultimos_30_dias']:
            for fechamento in fechamentos:
                meses = [
                    '', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
                ]
                dados_evolucao.append({
                    'data': f"{meses[fechamento.mes]}/{fechamento.ano}",
                    'saldo': float(fechamento.saldo_final)
                })
        else:
            # Evolução mensal baseada em transações
            saldo_acumulado = 0
            data_atual = data_inicio.replace(day=1)  # Primeiro dia do mês
            
            while data_atual <= data_fim:
                # Último dia do mês
                if data_atual.month == 12:
                    fim_mes = data_atual.replace(year=data_atual.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    fim_mes = data_atual.replace(month=data_atual.month + 1, day=1) - timedelta(days=1)
                
                # Ajustar para não ultrapassar o período
                if fim_mes > data_fim:
                    fim_mes = data_fim
                
                # Calcular receitas e despesas do mês
                receitas_mes = Transacao.objects.filter(
                    tipo='receita',
                    data__gte=data_atual,
                    data__lte=fim_mes
                ).aggregate(total=Sum('valor'))['total'] or 0
                
                despesas_mes = Transacao.objects.filter(
                    tipo='despesa',
                    data__gte=data_atual,
                    data__lte=fim_mes
                ).aggregate(total=Sum('valor'))['total'] or 0
                
                saldo_acumulado += float(receitas_mes) - float(despesas_mes)
                
                meses = [
                    '', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
                ]
                
                dados_evolucao.append({
                    'data': f"{meses[data_atual.month]}/{data_atual.year}",
                    'saldo': saldo_acumulado
                })
                
                # Próximo mês
                if data_atual.month == 12:
                    data_atual = data_atual.replace(year=data_atual.year + 1, month=1)
                else:
                    data_atual = data_atual.replace(month=data_atual.month + 1)
                
                if data_atual > data_fim:
                    break
    
    # Serializar dados para JSON (necessário para os gráficos)
    dados_categorias_json = json.dumps(dados_categorias)
    dados_evolucao_json = json.dumps(dados_evolucao)
    
    context = {
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo': saldo,
        'dados_categorias': dados_categorias,
        'dados_evolucao': dados_evolucao,
        'dados_categorias_json': dados_categorias_json,
        'dados_evolucao_json': dados_evolucao_json,
        'periodo': periodo,
        'tipo_exibicao': tipo_exibicao,
        'data_inicio': data_inicio_param or '',
        'data_fim': data_fim_param or '',
    }
    return render(request, 'financas/relatorios.html', context)



def fechamento_mensal(request):
    from datetime import datetime
    from django.db.models import Sum
    from django.contrib import messages
    from .models import ConfiguracaoFechamento
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'fechar_conta':
            mes = int(request.POST.get('mes'))
            ano = int(request.POST.get('ano'))
            conta_id = request.POST.get('conta_id')
            
            conta = Conta.objects.get(id=conta_id)
            
            # Verificar configurações de fechamento
            config = ConfiguracaoFechamento.get_configuracao()
            pode_fechar, motivo = config.pode_fechar_mes(ano, mes)
            
            if not pode_fechar:
                messages.error(request, f'Fechamento não permitido: {motivo}')
                return redirect('fechamento_mensal')
            
            # Verificar se já existe fechamento para este mês/ano/conta
            if FechamentoMensal.objects.filter(mes=mes, ano=ano, conta=conta).exists():
                messages.error(request, f'Fechamento para {mes}/{ano} da conta {conta.nome} já existe!')
            else:
                # Calcular totais do mês
                data_inicio = datetime(ano, mes, 1).date()
                if mes == 12:
                    data_fim = datetime(ano + 1, 1, 1).date()
                else:
                    data_fim = datetime(ano, mes + 1, 1).date()
                
                # Verificar se é fechamento antecipado
                import calendar
                ultimo_dia_mes_fechamento = calendar.monthrange(ano, mes)[1]
                data_fechamento_atual = datetime.now().date()
                eh_fechamento_antecipado_post = (
                    ano == data_fechamento_atual.year and 
                    mes == data_fechamento_atual.month and 
                    data_fechamento_atual.day < ultimo_dia_mes_fechamento
                )
                
                # Definir período real considerado
                if eh_fechamento_antecipado_post:
                    data_fim_real = data_fechamento_atual
                else:
                    data_fim_real = data_fim - timedelta(days=1)
                
                transacoes_mes = Transacao.objects.filter(
                    data__gte=data_inicio,
                    data__lte=data_fim_real,
                    conta=conta
                )
                
                receitas = transacoes_mes.filter(tipo='receita').aggregate(
                    total=Sum('valor')
                )['total'] or 0
                
                despesas = transacoes_mes.filter(tipo='despesa').aggregate(
                    total=Sum('valor')
                )['total'] or 0
                
                # Calcular saldo inicial (fechamento anterior ou zero)
                fechamento_anterior = FechamentoMensal.objects.filter(
                    conta=conta,
                    ano__lt=ano
                ).order_by('-ano', '-mes').first()
                
                if not fechamento_anterior:
                    fechamento_anterior = FechamentoMensal.objects.filter(
                        conta=conta,
                        ano=ano, 
                        mes__lt=mes
                    ).order_by('-mes').first()
                
                # CORREÇÃO: Se não há fechamento anterior, saldo inicial deve ser 0
                # porque as transações já estão refletidas no saldo atual da conta
                saldo_inicial = fechamento_anterior.saldo_final if fechamento_anterior else Decimal('0.00')
                saldo_final = saldo_inicial + receitas - despesas
                
                # Desabilitar atualização automática de saldo durante fechamento
                from .signals import desabilitar_atualizacao_saldo, habilitar_atualizacao_saldo
                desabilitar_atualizacao_saldo()
                
                try:
                    # Criar fechamento
                    FechamentoMensal.objects.create(
                        mes=mes,
                        ano=ano,
                        conta=conta,
                        saldo_inicial=saldo_inicial,
                        total_receitas=receitas,
                        total_despesas=despesas,
                        saldo_final=saldo_final,
                        fechado=True,
                        eh_parcial=eh_fechamento_antecipado_post,
                        data_inicio_periodo=data_inicio,
                        data_fim_periodo=data_fim_real,
                        data_fechamento=datetime.now()
                    )
                    
                    # Atualizar saldo da conta manualmente após fechamento
                    conta.saldo = saldo_final
                    conta.save()
                    
                finally:
                    # Reabilitar atualização automática de saldo
                    habilitar_atualizacao_saldo()
                
                messages.success(request, f'Fechamento de {mes}/{ano} para {conta.nome} realizado com sucesso!')
        
        return redirect('fechamento_mensal')
    
    # GET request - mostrar página
    contas = Conta.objects.all()
    
    # Obter configurações de fechamento
    config = ConfiguracaoFechamento.get_configuracao()
    
    # Dados do mês atual e anterior para exibição
    hoje = datetime.now()
    
    # Sempre mostrar o mês atual
    mes_atual = hoje.month
    ano_atual = hoje.year
    
    # Calcular mês anterior corretamente
    if mes_atual == 1:  # Janeiro
        mes_anterior = 12
        ano_anterior = ano_atual - 1
    else:
        mes_anterior = mes_atual - 1
        ano_anterior = ano_atual
    
    # Verificar se há parâmetros GET para navegação entre meses
    mes_solicitado = request.GET.get('mes')
    ano_solicitado = request.GET.get('ano')
    
    if mes_solicitado and ano_solicitado:
        try:
            mes_fechamento = int(mes_solicitado)
            ano_fechamento = int(ano_solicitado)
            # Validar se o mês está no range válido
            if not (1 <= mes_fechamento <= 12):
                raise ValueError("Mês inválido")
        except (ValueError, TypeError):
            # Se parâmetros inválidos, usar configuração padrão
            if config.permitir_fechamento_apenas_mes_anterior:
                mes_fechamento = mes_anterior
                ano_fechamento = ano_anterior
            else:
                mes_fechamento = mes_atual
                ano_fechamento = ano_atual
    else:
        # Determinar qual mês será usado para fechamento baseado nas configurações
        if config.permitir_fechamento_apenas_mes_anterior:
            mes_fechamento = mes_anterior
            ano_fechamento = ano_anterior
        else:
            # Permitir fechamento do mês atual (comportamento antigo)
            mes_fechamento = mes_atual
            ano_fechamento = ano_atual
    
    # Verificar se é fechamento antecipado (antes do último dia do mês)
    import calendar
    ultimo_dia_mes = calendar.monthrange(ano_fechamento, mes_fechamento)[1]
    
    # Para mês anterior, nunca é fechamento antecipado
    if config.permitir_fechamento_apenas_mes_anterior:
        eh_fechamento_antecipado = False
    else:
        eh_fechamento_antecipado = hoje.day < ultimo_dia_mes
    
    meses_portugues = [
        '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    
    # Preparar dados das contas com status de fechamento
    contas_dados = []
    for conta in contas:
        # Verificar se já foi fechada no mês de fechamento
        fechamento_atual = FechamentoMensal.objects.filter(
            conta=conta,
            mes=mes_fechamento,
            ano=ano_fechamento
        ).first()
        
        status = 'Fechado' if fechamento_atual else 'Aberto'
        
        # Calcular valores do mês de fechamento (para mostrar o que seria fechado)
        valores_mes_fechamento = None
        periodo_fechamento = None
        if not fechamento_atual:  # Só calcular se ainda não foi fechado
            data_inicio = datetime(ano_fechamento, mes_fechamento, 1).date()
            if mes_fechamento == 12:
                data_fim = datetime(ano_fechamento + 1, 1, 1).date()
            else:
                data_fim = datetime(ano_fechamento, mes_fechamento + 1, 1).date()
            
            # Definir período considerado no fechamento
            if eh_fechamento_antecipado:
                data_fim_real = hoje.date()  # Se fechamento antecipado, até hoje
            else:
                data_fim_real = data_fim - timedelta(days=1)  # Último dia do mês
            
            periodo_fechamento = {
                'data_inicio': data_inicio,
                'data_fim': data_fim_real,
                'eh_antecipado': eh_fechamento_antecipado,
                'dias_considerados': (data_fim_real - data_inicio).days + 1,
                'total_dias_mes': ultimo_dia_mes
            }
            
            transacoes_mes = Transacao.objects.filter(
                data__gte=data_inicio,
                data__lte=data_fim_real,
                conta=conta
            )
            
            receitas_mes = transacoes_mes.filter(tipo='receita').aggregate(
                total=Sum('valor')
            )['total'] or 0
            
            despesas_mes = transacoes_mes.filter(tipo='despesa').aggregate(
                total=Sum('valor')
            )['total'] or 0
            
            # Calcular saldo inicial (fechamento anterior ou saldo da conta)
            fechamento_anterior = FechamentoMensal.objects.filter(
                conta=conta,
                ano__lt=ano_fechamento
            ).order_by('-ano', '-mes').first()
            
            if not fechamento_anterior:
                fechamento_anterior = FechamentoMensal.objects.filter(
                    conta=conta,
                    ano=ano_fechamento, 
                    mes__lt=mes_fechamento
                ).order_by('-mes').first()
            
            saldo_inicial_calculado = fechamento_anterior.saldo_final if fechamento_anterior else conta.saldo
            saldo_final_calculado = saldo_inicial_calculado + receitas_mes - despesas_mes
            
            valores_mes_fechamento = {
                'saldo_inicial': saldo_inicial_calculado,
                'receitas': receitas_mes,
                'despesas': despesas_mes,
                'saldo_final': saldo_final_calculado
            }
        
        # Buscar histórico de fechamentos desta conta (excluindo o mês de fechamento se existir)
        historico = FechamentoMensal.objects.filter(
            conta=conta
        ).exclude(
            mes=mes_fechamento, ano=ano_fechamento
        ).order_by('-ano', '-mes')[:6]  # Últimos 6 fechamentos
        
        # Verificar se há transações após o último fechamento
        transacoes_pos_fechamento = []
        ultimo_fechamento = FechamentoMensal.objects.filter(
            conta=conta
        ).order_by('-ano', '-mes').first()
        
        if ultimo_fechamento and ultimo_fechamento.data_fim_periodo:
            # Buscar transações após a data de fim do último fechamento
            transacoes_pos_fechamento = Transacao.objects.filter(
                conta=conta,
                data__gt=ultimo_fechamento.data_fim_periodo
            ).order_by('-data')[:10]  # Últimas 10 transações pós-fechamento
        
        contas_dados.append({
            'conta': conta,
            'status': status,
            'fechamento_atual': fechamento_atual,
            'valores_mes_fechamento': valores_mes_fechamento,
            'periodo_fechamento': periodo_fechamento,
            'historico': historico,
            'transacoes_pos_fechamento': transacoes_pos_fechamento,
            'ultimo_fechamento': ultimo_fechamento
        })
    
    # Verificar se pode fechar baseado nas configurações
    pode_fechar_mes, motivo_restricao = config.pode_fechar_mes(ano_fechamento, mes_fechamento)
    
    context = {
        'contas_dados': contas_dados,
        'mes_fechamento': mes_fechamento,
        'ano_fechamento': ano_fechamento,
        'mes_atual': mes_atual,
        'ano_atual': ano_atual,
        'mes_anterior': mes_anterior,
        'ano_anterior': ano_anterior,
        'meses_portugues': meses_portugues,
        'nome_mes_atual': meses_portugues[mes_atual],
        'nome_mes_fechamento': meses_portugues[mes_fechamento],
        'eh_fechamento_antecipado': eh_fechamento_antecipado,
        'dia_atual': hoje.day,
        'ultimo_dia_mes': ultimo_dia_mes,
        'config_fechamento': config,
        'pode_fechar_mes': pode_fechar_mes,
        'motivo_restricao': motivo_restricao,
        'eh_fechamento_mes_anterior': (mes_fechamento == mes_anterior and ano_fechamento == ano_anterior),
    }
    
    return render(request, 'financas/fechamento_mensal.html', context)

@login_required
def executar_fechamento_automatico(request):
    """
    Executa o fechamento automático de todas as contas elegíveis
    baseado nas configurações definidas.
    """
    from django.contrib import messages
    from django.http import JsonResponse
    
    config = ConfiguracaoFechamento.get_configuracao()
    
    # Verificar se o fechamento automático está habilitado
    if not config.fechamento_automatico:
        return JsonResponse({
            'success': False, 
            'message': 'Fechamento automático não está habilitado nas configurações.'
        })
    
    hoje = timezone.now().date()
    
    # Determinar qual mês fechar baseado nas configurações
    if config.permitir_fechamento_apenas_mes_anterior:
        # Só pode fechar mês anterior no dia 1
        if hoje.day != 1:
            return JsonResponse({
                'success': False,
                'message': f'Fechamento automático só pode ser executado no dia 1 do mês. Hoje é dia {hoje.day}.'
            })
        
        # Calcular mês anterior
        if hoje.month == 1:
            mes_fechamento = 12
            ano_fechamento = hoje.year - 1
        else:
            mes_fechamento = hoje.month - 1
            ano_fechamento = hoje.year
    else:
        # Pode fechar mês atual
        mes_fechamento = hoje.month
        ano_fechamento = hoje.year
    
    # Verificar se pode fechar o mês
    pode_fechar, motivo = config.pode_fechar_mes(ano_fechamento, mes_fechamento)
    if not pode_fechar:
        return JsonResponse({
            'success': False,
            'message': f'Não é possível executar fechamento automático: {motivo}'
        })
    
    # Buscar contas do usuário que ainda não foram fechadas no período
    contas = Conta.objects.filter(usuario=request.user)
    contas_fechadas = []
    contas_ja_fechadas = []
    erros = []
    
    for conta in contas:
        # Verificar se já existe fechamento para esta conta no período
        fechamento_existente = FechamentoMensal.objects.filter(
            conta=conta,
            mes=mes_fechamento,
            ano=ano_fechamento
        ).first()
        
        if fechamento_existente:
            contas_ja_fechadas.append(conta.nome)
            continue
        
        try:
            # Calcular período de fechamento
            data_inicio = datetime(ano_fechamento, mes_fechamento, 1).date()
            if mes_fechamento == 12:
                data_fim = datetime(ano_fechamento + 1, 1, 1).date()
            else:
                data_fim = datetime(ano_fechamento, mes_fechamento + 1, 1).date()
            
            # Determinar se é fechamento antecipado
            ultimo_dia_mes = (data_fim - timedelta(days=1)).day
            eh_fechamento_antecipado = hoje.day < ultimo_dia_mes if not config.permitir_fechamento_apenas_mes_anterior else False
            
            # Calcular receitas e despesas do período
            receitas_mes = Transacao.objects.filter(
                conta=conta,
                tipo='receita',
                data__gte=data_inicio,
                data__lt=data_fim
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            
            despesas_mes = Transacao.objects.filter(
                conta=conta,
                tipo='despesa',
                data__gte=data_inicio,
                data__lt=data_fim
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            
            # Calcular saldo inicial
            fechamento_anterior = FechamentoMensal.objects.filter(
                conta=conta,
                ano__lt=ano_fechamento
            ).order_by('-ano', '-mes').first()
            
            if not fechamento_anterior:
                fechamento_anterior = FechamentoMensal.objects.filter(
                    conta=conta,
                    ano=ano_fechamento,
                    mes__lt=mes_fechamento
                ).order_by('-mes').first()
            
            saldo_inicial = fechamento_anterior.saldo_final if fechamento_anterior else conta.saldo
            saldo_final = saldo_inicial + receitas_mes - despesas_mes
            
            # Desabilitar atualização automática de saldo durante fechamento
            from .signals import desabilitar_atualizacao_saldo, habilitar_atualizacao_saldo
            desabilitar_atualizacao_saldo()
            
            try:
                # Criar fechamento
                fechamento = FechamentoMensal.objects.create(
                    conta=conta,
                    mes=mes_fechamento,
                    ano=ano_fechamento,
                    saldo_inicial=saldo_inicial,
                    receitas=receitas_mes,
                    despesas=despesas_mes,
                    saldo_final=saldo_final,
                    data_fechamento=hoje,
                    fechamento_antecipado=eh_fechamento_antecipado
                )
                
                # Atualizar saldo da conta manualmente após fechamento
                conta.saldo = saldo_final
                conta.save()
                
            finally:
                # Reabilitar atualização automática de saldo
                habilitar_atualizacao_saldo()
            
            contas_fechadas.append(conta.nome)
            
        except Exception as e:
            erros.append(f'{conta.nome}: {str(e)}')
    
    # Preparar resposta
    resultado = {
        'success': True,
        'mes_fechamento': mes_fechamento,
        'ano_fechamento': ano_fechamento,
        'contas_fechadas': contas_fechadas,
        'contas_ja_fechadas': contas_ja_fechadas,
        'erros': erros,
        'total_fechadas': len(contas_fechadas)
    }
    
    return JsonResponse(resultado)

def test_filter(request):
    """View de teste para filtros"""
    return render(request, 'financas/test_filter.html')

@login_required
def compartilhar_whatsapp(request):
    """
    Gera resumo financeiro formatado para compartilhamento via WhatsApp.
    """
    try:
        # Data atual para cálculos
        hoje = timezone.now().date()
        
        # Obter resumo financeiro consolidado
        total_receitas = Decimal('0.00')
        total_despesas = Decimal('0.00')
        saldo_atual_total = Decimal('0.00')
        
        contas = Conta.objects.all()
        
        for conta in contas:
            try:
                resumo = ContaService.obter_resumo_financeiro(
                    conta.id, 
                    mes=hoje.month, 
                    ano=hoje.year
                )
                total_receitas += resumo['receitas']
                total_despesas += resumo['despesas']
                saldo_atual_total += resumo['saldo_atual']
            except Exception as e:
                logger.error(f"Erro ao obter resumo da conta {conta.id}: {e}")
                continue
        
        # Obter transações recentes (últimos 7 dias)
        data_inicio = hoje - timedelta(days=7)
        transacoes_recentes = Transacao.objects.select_related('categoria', 'conta').filter(
            data__gte=data_inicio,
            despesa_parcelada__isnull=True
        ).order_by('-data', '-id')[:10]
        
        # Obter maiores despesas do mês
        primeiro_dia_mes = hoje.replace(day=1)
        maiores_despesas = Transacao.objects.select_related('categoria').filter(
            data__gte=primeiro_dia_mes,
            tipo='despesa',
            despesa_parcelada__isnull=True
        ).order_by('-valor')[:5]
        
        # Formatear texto para WhatsApp
        # Nomes dos meses em português
        meses_portugues = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        mes_nome = meses_portugues[hoje.month - 1]
        texto_whatsapp = f"💰 *RESUMO FINANCEIRO - {mes_nome.upper()}/{hoje.year}*\n\n"
        texto_whatsapp += f"📊 *SALDO GERAL*\n"
        texto_whatsapp += f"💚 Receitas: R$ {total_receitas:,.2f}\n"
        texto_whatsapp += f"❌ Despesas: R$ {total_despesas:,.2f}\n"
        texto_whatsapp += f"💰 Saldo Atual: R$ {saldo_atual_total:,.2f}\n\n"
        
        if transacoes_recentes:
            texto_whatsapp += f"📋 *TRANSAÇÕES RECENTES (últimos 7 dias)*\n"
            for transacao in transacoes_recentes:
                emoji = "💚" if transacao.tipo == 'receita' else "❌"
                texto_whatsapp += f"{emoji} {transacao.descricao}: R$ {transacao.valor:,.2f}\n"
            texto_whatsapp += "\n"
        
        if maiores_despesas:
            texto_whatsapp += f"🔥 *MAIORES DESPESAS DO MÊS*\n"
            for despesa in maiores_despesas:
                categoria = despesa.categoria.nome if despesa.categoria else 'Sem categoria'
                texto_whatsapp += f"• {despesa.descricao} ({categoria}): R$ {despesa.valor:,.2f}\n"
            texto_whatsapp += "\n"
        
        texto_whatsapp += f"📱 Gerado pelo Sistema Financeiro em {hoje.strftime('%d/%m/%Y')}"
        
        # Retornar JSON com o texto formatado
        return JsonResponse({
            'success': True,
            'texto': texto_whatsapp,
            'resumo': {
                'receitas': float(total_receitas),
                'despesas': float(total_despesas),
                'saldo': float(saldo_atual_total),
                'transacoes_recentes': len(transacoes_recentes),
                'maiores_despesas': len(maiores_despesas)
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar resumo para WhatsApp: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro ao gerar resumo financeiro'
        }, status=500)


# Views para Reset de Senha
from .models import PasswordResetToken
from .validators import django_validar_senha_forte

def esqueci_senha_view(request):
    """
    View para solicitar reset de senha.
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Por favor, informe seu email.')
            return render(request, 'financas/esqueci_senha.html')
        
        try:
            user = CustomUser.objects.get(email=email, is_active=True)
            
            # Invalidar tokens anteriores
            PasswordResetToken.objects.filter(user=user, usado=False).update(usado=True)
            
            # Gerar novo token
            token = get_random_string(50)
            expira_em = timezone.now() + timedelta(hours=1)  # Token válido por 1 hora
            
            reset_token = PasswordResetToken.objects.create(
                user=user,
                token=token,
                expira_em=expira_em
            )
            
            # Enviar email
            reset_url = request.build_absolute_uri(
                reverse('reset_senha', kwargs={'token': token})
            )
            
            subject = 'Recuperação de Senha - Sistema Financeiro'
            message = f'''
Olá {user.get_nome_completo()},

Você solicitou a recuperação de sua senha.

Clique no link abaixo para criar uma nova senha:
{reset_url}

Este link é válido por 1 hora.

Se você não solicitou esta recuperação, ignore este email.

Atenciosamente,
Equipe Sistema Financeiro
            '''
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Instruções para recuperação de senha foram enviadas para seu email.')
                return redirect('login')
            except Exception as e:
                logger.error(f"Erro ao enviar email de recuperação: {str(e)}")
                messages.error(request, 'Erro ao enviar email. Tente novamente mais tarde.')
                
        except CustomUser.DoesNotExist:
            # Por segurança, não informamos se o email existe ou não
            messages.success(request, 'Se o email estiver cadastrado, você receberá as instruções para recuperação.')
            return redirect('login')
    
    return render(request, 'financas/esqueci_senha.html')

def reset_senha_view(request, token):
    """
    View para redefinir senha com token.
    """
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if not reset_token.is_valid():
            messages.error(request, 'Token inválido ou expirado. Solicite uma nova recuperação de senha.')
            return redirect('esqueci_senha')
        
        if request.method == 'POST':
            nova_senha = request.POST.get('nova_senha')
            confirmar_senha = request.POST.get('confirmar_senha')
            
            if not nova_senha or not confirmar_senha:
                messages.error(request, 'Por favor, preencha todos os campos.')
                return render(request, 'financas/reset_senha.html', {'token': token})
            
            if nova_senha != confirmar_senha:
                messages.error(request, 'As senhas não coincidem.')
                return render(request, 'financas/reset_senha.html', {'token': token})
            
            # Validar senha forte
            try:
                django_validar_senha_forte(nova_senha)
            except ValidationError as e:
                messages.error(request, str(e))
                return render(request, 'financas/reset_senha.html', {'token': token})
            
            # Atualizar senha
            user = reset_token.user
            user.set_password(nova_senha)
            user.save()
            
            # Marcar token como usado
            reset_token.marcar_como_usado()
            
            messages.success(request, 'Senha alterada com sucesso! Você já pode fazer login.')
            return redirect('login')
        
        return render(request, 'financas/reset_senha.html', {'token': token})
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Token inválido. Solicite uma nova recuperação de senha.')
        return redirect('esqueci_senha')

# Views de Registro de Usuário
# Imports já movidos para o topo do arquivo

def registro_view(request):
    """
    View para registro de novos usuários com validação de email.
    """
    if request.method == 'POST':
        # Obter dados do formulário
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        tipo_pessoa = request.POST.get('tipo_pessoa')
        cpf = request.POST.get('cpf', '').strip()
        cnpj = request.POST.get('cnpj', '').strip()
        
        # Validações básicas
        if password1 != password2:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'financas/registro.html')
        
        # Validar senha forte
        try:
            django_validar_senha_forte(password1)
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'financas/registro.html')
        
        # Verificar se usuário já existe
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Nome de usuário já existe.')
            return render(request, 'financas/registro.html')
        
        # Verificar email apenas para usuários verificados
        existing_email_user = CustomUser.objects.filter(email=email).first()
        if existing_email_user:
            if existing_email_user.email_verificado:
                messages.error(request, 'Email já está em uso por um usuário verificado.')
                return render(request, 'financas/registro.html')
            else:
                # Remove usuário não verificado com mesmo email
                existing_email_user.delete()
                messages.info(request, 'Registro anterior com este email foi removido. Prosseguindo com novo cadastro.')
        
        # Validar CPF/CNPJ baseado no tipo de pessoa
        from .validators import validar_cpf, validar_cnpj
        
        if tipo_pessoa == 'fisica':
            if not cpf:
                messages.error(request, 'CPF é obrigatório para pessoa física.')
                return render(request, 'financas/registro.html')
            
            if not validar_cpf(cpf):
                messages.error(request, 'CPF inválido.')
                return render(request, 'financas/registro.html')
            
            # Verificar se CPF já existe
            cpf_limpo = re.sub(r'\D', '', cpf)
            existing_user = CustomUser.objects.filter(cpf=cpf_limpo).first()
            if existing_user:
                if existing_user.email_verificado:
                    messages.error(request, 'CPF já está cadastrado e verificado.')
                    return render(request, 'financas/registro.html')
                else:
                    # Remove usuário não verificado para permitir novo registro
                    existing_user.delete()
                    messages.info(request, 'Registro anterior não verificado foi removido. Prosseguindo com novo cadastro.')
        
        elif tipo_pessoa == 'juridica':
            if not cnpj:
                messages.error(request, 'CNPJ é obrigatório para pessoa jurídica.')
                return render(request, 'financas/registro.html')
            
            if not validar_cnpj(cnpj):
                messages.error(request, 'CNPJ inválido.')
                return render(request, 'financas/registro.html')
            
            # Verificar se CNPJ já existe
            cnpj_limpo = re.sub(r'\D', '', cnpj)
            existing_user = CustomUser.objects.filter(cnpj=cnpj_limpo).first()
            if existing_user:
                if existing_user.email_verificado:
                    messages.error(request, 'CNPJ já está cadastrado e verificado.')
                    return render(request, 'financas/registro.html')
                else:
                    # Remove usuário não verificado para permitir novo registro
                    existing_user.delete()
                    messages.info(request, 'Registro anterior não verificado foi removido. Prosseguindo com novo cadastro.')
        
        # Verificar se já existe um usuário com o mesmo schema_name que seria gerado
        if tipo_pessoa == 'fisica' and cpf:
            schema_name_esperado = f"user_{re.sub(r'\D', '', cpf)}"
        elif tipo_pessoa == 'juridica' and cnpj:
            schema_name_esperado = f"user_{re.sub(r'\D', '', cnpj)}"
        else:
            schema_name_esperado = None
            
        if schema_name_esperado:
            existing_schema_user = CustomUser.objects.filter(schema_name=schema_name_esperado).first()
            if existing_schema_user:
                if existing_schema_user.email_verificado:
                    messages.error(request, 'Já existe um usuário verificado com este documento.')
                    return render(request, 'financas/registro.html')
                else:
                    # Remove usuário não verificado para permitir novo registro
                    existing_schema_user.delete()
                    messages.info(request, 'Registro anterior não verificado foi removido. Prosseguindo com novo cadastro.')
        
        try:
            # Criar usuário
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password1,
                tipo_pessoa=tipo_pessoa,
                is_active=False  # Usuário inativo até confirmar email
            )
            
            # Definir CPF ou CNPJ
            if tipo_pessoa == 'fisica':
                user.cpf = re.sub(r'\D', '', cpf)
            else:
                user.cnpj = re.sub(r'\D', '', cnpj)
                # Buscar dados da Receita Federal se for CNPJ
                try:
                    from .validators import buscar_dados_cnpj
                    dados_cnpj = buscar_dados_cnpj(user.cnpj)
                    if dados_cnpj:
                        user.razao_social = dados_cnpj.get('nome', '')
                        user.nome_fantasia = dados_cnpj.get('fantasia', '')
                        user.endereco_logradouro = dados_cnpj.get('logradouro', '')
                        user.endereco_numero = dados_cnpj.get('numero', '')
                        user.endereco_complemento = dados_cnpj.get('complemento', '')
                        user.endereco_bairro = dados_cnpj.get('bairro', '')
                        user.endereco_municipio = dados_cnpj.get('municipio', '')
                        user.endereco_uf = dados_cnpj.get('uf', '')
                        user.endereco_cep = dados_cnpj.get('cep', '')
                        user.telefone = dados_cnpj.get('telefone', '')
                except Exception as e:
                    logger.warning(f"Erro ao buscar dados do CNPJ {user.cnpj}: {str(e)}")
            
            # Gerar código de verificação de 6 dígitos
            import random
            from datetime import datetime, timedelta
            
            codigo = str(random.randint(100000, 999999))
            user.codigo_verificacao = codigo
            user.codigo_verificacao_expira = timezone.now() + timedelta(minutes=15)  # Expira em 15 minutos
            user.save()
            
            # Enviar email com código de verificação
            enviar_codigo_verificacao(user, request)
            
            # Armazenar ID do usuário na sessão para a próxima etapa
            request.session['user_id_verificacao'] = user.id
            
            messages.success(request, 'Código de verificação enviado para seu email!')
            return redirect('verificar_codigo')
            
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {str(e)}")
            messages.error(request, 'Erro interno. Tente novamente.')
            return render(request, 'financas/registro.html')
    
    return render(request, 'financas/registro.html')

def enviar_codigo_verificacao(user, request):
    """
    Envia código de verificação para o usuário.
    """
    codigo = user.codigo_verificacao
    
    assunto = 'Código de Verificação - Sistema Financeiro'
    mensagem = f"""
    Olá {user.get_nome_completo() or user.username},
    
    Seu código de verificação é: {codigo}
    
    Este código expira em 15 minutos.
    
    Se você não se cadastrou em nosso sistema, ignore este email.
    
    Atenciosamente,
    Equipe Sistema Financeiro
    """
    
    try:
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        logger.info(f"Código de verificação enviado para {user.email}")
    except Exception as e:
        logger.error(f"Erro ao enviar código de verificação para {user.email}: {str(e)}")
        raise

def verificar_codigo_view(request):
    """
    View para verificar o código de verificação inserido pelo usuário.
    """
    if request.method == 'POST':
        codigo_inserido = request.POST.get('codigo', '').strip()
        user_id = request.session.get('user_id_verificacao')
        
        if not user_id:
            messages.error(request, 'Sessão expirada. Faça o cadastro novamente.')
            return redirect('registro')
        
        try:
            user = CustomUser.objects.get(id=user_id, is_active=False)
            
            # Verificar se o código não expirou
            from django.utils import timezone
            if user.codigo_verificacao_expira and timezone.now() > user.codigo_verificacao_expira:
                messages.error(request, 'Código de verificação expirado. Solicite um novo código.')
                return render(request, 'financas/verificar_codigo.html')
            
            # Verificar se o código está correto
            if user.codigo_verificacao == codigo_inserido:
                # Ativar usuário e limpar código
                user.is_active = True
                user.email_verificado = True
                user.codigo_verificacao = ''
                user.codigo_verificacao_expira = None
                user.save()
                
                # Limpar sessão
                del request.session['user_id_verificacao']
                
                # Fazer login automático
                from django.contrib.auth import login as auth_login
                auth_login(request, user)
                
                messages.success(request, 'Conta ativada com sucesso! Bem-vindo ao sistema!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Código de verificação inválido.')
                return render(request, 'financas/verificar_codigo.html')
                
        except CustomUser.DoesNotExist:
            messages.error(request, 'Usuário não encontrado. Faça o cadastro novamente.')
            return redirect('registro')
    
    return render(request, 'financas/verificar_codigo.html')

def reenviar_codigo_view(request):
    """
    View para reenviar código de verificação.
    """
    user_id = request.session.get('user_id_verificacao')
    
    if not user_id:
        messages.error(request, 'Sessão expirada. Faça o cadastro novamente.')
        return redirect('registro')
    
    try:
        user = CustomUser.objects.get(id=user_id, is_active=False)
        
        # Gerar novo código
        import random
        from datetime import datetime, timedelta
        
        codigo = str(random.randint(100000, 999999))
        user.codigo_verificacao = codigo
        user.codigo_verificacao_expira = timezone.now() + timedelta(minutes=15)
        user.save()
        
        # Enviar novo código
        enviar_codigo_verificacao(user, request)
        
        messages.success(request, 'Novo código de verificação enviado!')
        return redirect('verificar_codigo')
        
    except CustomUser.DoesNotExist:
        messages.error(request, 'Usuário não encontrado. Faça o cadastro novamente.')
        return redirect('registro')

def confirmar_email_view(request, token):
    """
    View para confirmar email do usuário (mantida para compatibilidade).
    """
    try:
        user = CustomUser.objects.get(token_verificacao=token, is_active=False)
        user.is_active = True
        user.email_verificado = True
        user.token_verificacao = ''  # Limpar token
        user.save()
        
        messages.success(request, 'Email confirmado com sucesso! Você já pode fazer login.')
        return redirect('login')
        
    except CustomUser.DoesNotExist:
        messages.error(request, 'Token inválido ou expirado.')
        return redirect('registro')

def buscar_cnpj_view(request):
    """
    View AJAX para buscar dados do CNPJ na Receita Federal.
    """
    if request.method == 'GET':
        cnpj = request.GET.get('cnpj', '').strip()
        
        if not cnpj:
            return JsonResponse({'error': 'CNPJ não informado'}, status=400)
        
        # Validar CNPJ
        from .validators import validar_cnpj, buscar_dados_cnpj
        
        if not validar_cnpj(cnpj):
            return JsonResponse({'error': 'CNPJ inválido'}, status=400)
        
        try:
            dados = buscar_dados_cnpj(cnpj)
            if dados:
                return JsonResponse({
                    'success': True,
                    'dados': dados
                })
            else:
                return JsonResponse({'error': 'CNPJ não encontrado'}, status=404)
                
        except Exception as e:
            logger.error(f"Erro ao buscar CNPJ {cnpj}: {str(e)}")
            return JsonResponse({'error': 'Erro ao consultar CNPJ'}, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

def login_view(request):
    """View de login personalizada para a aplicação financas."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            from django.contrib.auth import authenticate, login as auth_login
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                messages.error(request, 'Usuário ou senha inválidos.')
        else:
            messages.error(request, 'Por favor, preencha todos os campos.')
    
    return render(request, 'financas/login.html')

@login_required
@require_http_methods(["POST"])
def marcar_parcela_paga(request, transacao_id):
    """Marca uma parcela como paga."""
    try:
        transacao = get_object_or_404(Transacao.objects, id=transacao_id, despesa_parcelada__isnull=False)
        transacao.marcar_como_pago()
        messages.success(request, f"Parcela marcada como paga em {transacao.data_pagamento.strftime('%d/%m/%Y')}")
        
    except Exception as e:
        messages.error(request, f"Erro ao marcar parcela como paga: {str(e)}")
    
    return redirect('detalhes_despesa_parcelada', despesa_id=transacao.despesa_parcelada.id)

@require_http_methods(["POST"])
def processar_pagamento_parcela(request, transacao_id):
    """Processa o pagamento de uma parcela com validação de mês fechado."""
    from .utils import verificar_mes_fechado
    from decimal import Decimal
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Processando pagamento da parcela {transacao_id}")
    logger.info(f"Dados POST: {request.POST}")
    
    try:
        transacao = get_object_or_404(Transacao.objects, id=transacao_id, despesa_parcelada__isnull=False)
        
        # Obter dados do formulário
        data_pagamento_str = request.POST.get('data_pagamento')
        valor_pago_str = request.POST.get('valor_pago')
        
        if not data_pagamento_str or not valor_pago_str:
            messages.error(request, "Data de pagamento e valor são obrigatórios.")
            return redirect('detalhes_despesa_parcelada', despesa_id=transacao.despesa_parcelada.id)
        
        # Converter data
        from datetime import datetime
        data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date()
        
        # Verificar se a data não está no futuro
        from datetime import date
        if data_pagamento > date.today():
            messages.error(request, "Data de pagamento não pode ser no futuro.")
            return redirect('detalhes_despesa_parcelada', despesa_id=transacao.despesa_parcelada.id)
        
        # Verificar se o mês não está fechado
        mes_fechado, mensagem_fechamento = verificar_mes_fechado(data_pagamento, transacao.conta)
        if mes_fechado:
            messages.error(request, f"Não é possível registrar pagamento em {data_pagamento.strftime('%m/%Y')} pois o mês já foi fechado.")
            return redirect('detalhes_despesa_parcelada', despesa_id=transacao.despesa_parcelada.id)
        
        # Converter valor usando a função utilitária
        from .utils import parse_currency_value
        valor_pago = parse_currency_value(valor_pago_str)
        
        if valor_pago <= 0:
            messages.error(request, "Valor pago deve ser maior que zero.")
            return redirect('detalhes_despesa_parcelada', despesa_id=transacao.despesa_parcelada.id)
        
        if valor_pago > transacao.valor:
            messages.error(request, "Valor pago não pode ser maior que o valor da parcela.")
            return redirect('detalhes_despesa_parcelada', despesa_id=transacao.despesa_parcelada.id)
        
        # Processar pagamento
        if valor_pago == transacao.valor:
            # Pagamento total - marcar como pago e criar transação de pagamento
            transacao.pago = True
            transacao.data_pagamento = data_pagamento
            transacao.save()
            
            # Criar transação de pagamento automática
            transacao_pagamento = Transacao.objects.create(
                data=data_pagamento,
                descricao=f"Pagamento: {transacao.descricao}",
                valor=valor_pago,
                categoria=transacao.categoria,
                tipo='despesa',  # Pagamento é sempre uma despesa
                eh_parcelada=False,  # Transação de pagamento não é parcelada
                conta=transacao.conta,
                pago=True,
                data_pagamento=data_pagamento
            )
            
            messages.success(request, f"Parcela paga integralmente em {data_pagamento.strftime('%d/%m/%Y')}. Transação de pagamento criada automaticamente.")
            
        else:
            # Pagamento parcial - criar nova transação com o saldo
            saldo_restante = transacao.valor - valor_pago
            
            # Marcar transação atual como paga com valor parcial
            transacao.valor = valor_pago
            transacao.pago = True
            transacao.data_pagamento = data_pagamento
            transacao.save()
            
            # Criar transação de pagamento automática para o valor pago
            transacao_pagamento = Transacao.objects.create(
                data=data_pagamento,
                descricao=f"Pagamento parcial: {transacao.descricao}",
                valor=valor_pago,
                categoria=transacao.categoria,
                tipo='despesa',  # Pagamento é sempre uma despesa
                eh_parcelada=False,  # Transação de pagamento não é parcelada
                conta=transacao.conta,
                pago=True,
                data_pagamento=data_pagamento
            )
            
            # Criar nova transação para o saldo restante
            nova_transacao = Transacao.objects.create(
                data=transacao.data,
                descricao=f"{transacao.descricao} (Saldo restante)",
                valor=saldo_restante,
                categoria=transacao.categoria,
                tipo=transacao.tipo,
                eh_parcelada=True,
                transacao_pai=transacao.transacao_pai or transacao,
                numero_parcela=transacao.numero_parcela,
                total_parcelas=transacao.total_parcelas,
                conta=transacao.conta,
                despesa_parcelada=transacao.despesa_parcelada,
                pago=False
            )
            
            messages.success(request, 
                f"Pagamento parcial de R$ {valor_pago:.2f} registrado em {data_pagamento.strftime('%d/%m/%Y')}. "
                f"Saldo restante de R$ {saldo_restante:.2f} criado como nova parcela. Transação de pagamento criada automaticamente.")
        
        # Atualizar saldo da conta
        transacao.conta.atualizar_saldo()
        
    except ValueError as e:
        messages.error(request, "Formato de data ou valor inválido.")
    except Exception as e:
        messages.error(request, f"Erro ao processar pagamento: {str(e)}")
    
    return redirect('detalhes_despesa_parcelada', despesa_id=transacao.despesa_parcelada.id)

@login_required
@require_http_methods(["POST"])
def marcar_parcela_nao_paga(request, transacao_id):
    """Marca uma parcela como não paga e exclui a transação de pagamento correspondente."""
    try:
        transacao = get_object_or_404(Transacao.objects, id=transacao_id, despesa_parcelada__isnull=False)
        
        # Verificar se a parcela está paga
        if not transacao.pago or not transacao.data_pagamento:
            messages.warning(request, "Esta parcela já está marcada como não paga.")
            return redirect('detalhes_despesa_parcelada', despesa_id=transacao.despesa_parcelada.id)
        
        # Verificar se o mês da transação não está fechado
        from .utils import verificar_mes_fechado
        mes_fechado, _ = verificar_mes_fechado(transacao.data_pagamento, transacao.conta)
        if mes_fechado:
            messages.error(request, f"Não é possível alterar status de pagamento de {transacao.data_pagamento.strftime('%m/%Y')} pois o mês já foi fechado.")
            return redirect('detalhes_despesa_parcelada', despesa_id=transacao.despesa_parcelada.id)
        
        # Buscar e excluir a transação de pagamento correspondente
        data_pagamento = transacao.data_pagamento
        valor_pagamento = transacao.valor
        
        # Procurar transação de pagamento criada automaticamente
        transacao_pagamento = Transacao.objects.filter(
            data=data_pagamento,
            valor=valor_pagamento,
            categoria=transacao.categoria,
            conta=transacao.conta,
            tipo='despesa',
            eh_parcelada=False,
            pago=True,
            data_pagamento=data_pagamento
        ).filter(
            Q(descricao__startswith="Pagamento: ") | 
            Q(descricao__startswith="Pagamento parcial: ")
        ).first()
        
        if transacao_pagamento:
            transacao_pagamento.delete()
            messages.success(request, f"Parcela reaberta e transação de pagamento de {data_pagamento.strftime('%d/%m/%Y')} excluída com sucesso.")
        else:
            messages.success(request, "Parcela reaberta com sucesso.")
        
        # Marcar parcela como não paga
        transacao.marcar_como_nao_pago()
        
        # Atualizar saldo da conta
        transacao.conta.atualizar_saldo()
        
    except Exception as e:
        messages.error(request, f"Erro ao reabrir parcela: {str(e)}")
    
    return redirect('detalhes_despesa_parcelada', despesa_id=transacao.despesa_parcelada.id)

@login_required
@require_http_methods(["POST"])
def excluir_despesa_parcelada(request, despesa_id):
    """Exclui uma despesa parcelada e todas suas parcelas."""
    try:
        despesa_parcelada = get_object_or_404(DespesaParcelada.objects, id=despesa_id)
        
        if request.method == 'POST':
            # Verificar se existem parcelas pagas
            parcelas_pagas = Transacao.objects.filter(
                despesa_parcelada=despesa_parcelada,
                pago=True
            ).count()
            
            if parcelas_pagas > 0:
                # Criar contexto para modal de erro
                context = {
                    'erro_exclusao': True,
                    'despesa_nome': despesa_parcelada.descricao,
                    'parcelas_pagas': parcelas_pagas,
                    'despesa_id': despesa_id
                }
                return render(request, 'financas/erro_exclusao_despesa.html', context)
            
            descricao = despesa_parcelada.descricao
            despesa_parcelada.excluir_com_parcelas()
            messages.success(request, f"Despesa parcelada '{descricao}' e todas suas parcelas foram excluídas com sucesso")
            return redirect('despesas_parceladas')
            
    except Exception as e:
        messages.error(request, f"Erro ao excluir despesa parcelada: {str(e)}")
        return redirect('despesas_parceladas')

def test_form(request):
    """View de teste para formulário"""
    return render(request, 'financas/test_form.html')

# API Views
def api_resumo_financeiro(request):
    """API endpoint para resumo financeiro"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        # Calcular resumo financeiro do usuário
        hoje = timezone.now().date()
        
        # Obter todas as transações (sem filtro de usuário por enquanto)
        transacoes = Transacao.objects.all()
        
        # Calcular totais
        total_receitas = transacoes.filter(tipo='receita').aggregate(
            total=Sum('valor')
        )['total'] or 0
        
        total_despesas = transacoes.filter(tipo='despesa').aggregate(
            total=Sum('valor')
        )['total'] or 0
        
        # Calcular saldo total das contas (saldo inicial)
        contas = Conta.objects.all()
        saldo_total = Decimal('1000.00')  # Para o teste, usar valor fixo por enquanto
        
        # Transações do mês atual
        transacoes_mes = transacoes.filter(
            data__month=hoje.month,
            data__year=hoje.year
        ).count()
        
        data = {
            'total_receitas': float(total_receitas),
            'total_despesas': float(total_despesas),
            'saldo_total': float(saldo_total),
            'transacoes_mes': transacoes_mes
        }
        
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Erro na API de resumo financeiro: {e}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

def api_transacoes_por_categoria(request):
    """API endpoint para transações por categoria"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        hoje = timezone.now().date()
        
        # Obter transações do mês atual agrupadas por categoria
        transacoes = Transacao.objects.filter(
            data__year=hoje.year,
            data__month=hoje.month
        ).values('categoria__nome', 'categoria__cor').annotate(
            total=Sum('valor')
        ).order_by('-total')
        
        data = [
            {
                'categoria': t['categoria__nome'] or 'Sem categoria',
                'total': float(t['total']),
                'cor': t['categoria__cor'] or '#6c757d'
            }
            for t in transacoes
        ]
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.error(f"Erro na API transações por categoria: {e}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

def api_evolucao_saldo(request):
    """API endpoint para evolução do saldo"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        hoje = timezone.now().date()
        
        # Obter dados dos últimos 6 meses
        dados_evolucao = []
        
        for i in range(6):
            data_mes = hoje - relativedelta(months=i)
            
            # Calcular saldo total de todas as contas no final do mês
            saldo_total = Decimal('0.00')
            contas = Conta.objects.all()
            
            for conta in contas:
                # Saldo inicial da conta
                saldo_conta = Decimal('0.00')
                
                # Somar todas as transações até o final do mês
                transacoes = Transacao.objects.filter(
                    conta=conta,
                    data__lte=data_mes.replace(day=calendar.monthrange(data_mes.year, data_mes.month)[1])
                )
                
                for transacao in transacoes:
                    if transacao.tipo == 'receita':
                        saldo_conta += transacao.valor
                    else:
                        saldo_conta -= transacao.valor
                
                saldo_total += saldo_conta
            
            dados_evolucao.append({
                'data': data_mes.strftime('%m/%Y'),
                'saldo': float(saldo_total)
            })
        
        # Inverter para ordem cronológica
        dados_evolucao.reverse()
        
        return JsonResponse(dados_evolucao, safe=False)
    except Exception as e:
        logger.error(f"Erro na API evolução do saldo: {e}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

def api_transacoes_recentes(request):
    """API endpoint para transações recentes"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        limit = request.GET.get('limit', 10)
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 10
        
        transacoes = Transacao.objects.select_related('categoria', 'conta').order_by('-data')[:limit]
        
        data = [
            {
                'id': t.id,
                'descricao': t.descricao,
                'valor': float(t.valor),
                'tipo': t.tipo,
                'data': t.data.strftime('%d/%m/%Y'),
                'categoria': t.categoria.nome if t.categoria else 'Sem categoria',
                'conta': t.conta.nome if t.conta else 'Sem conta'
            }
            for t in transacoes
        ]
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.error(f"Erro na API transações recentes: {e}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

def excluir_transacao(request, transacao_id):
    """
    Exclui uma transação específica.
    """
    try:
        transacao = get_object_or_404(Transacao.objects, id=transacao_id)
        
        if request.method == 'POST':
            # Verificar se o mês da transação não está fechado
            from .utils import verificar_mes_fechado
            mes_fechado, _ = verificar_mes_fechado(transacao.data, transacao.conta)
            if mes_fechado:
                messages.error(request, f"Não é possível excluir transação de {transacao.data.strftime('%m/%Y')} pois o mês já foi fechado.")
                return redirect('transacoes')
            
            # Usar o service para excluir a transação
            try:
                TransacaoService.excluir_transacao(transacao_id)
                messages.success(request, SuccessMessages.TRANSACAO_EXCLUIDA)
                logger.info(f"Transação excluída com sucesso - ID: {transacao_id}")
                return redirect('transacoes')
                
            except TransacaoServiceError as e:
                logger.error(f"Erro do serviço ao excluir transação {transacao_id}: {str(e)}")
                messages.error(request, str(e))
                return redirect('transacoes')
        
        # GET request - mostrar confirmação
        context = {
            'transacao': transacao,
        }
        return render(request, 'financas/confirmar_exclusao_transacao.html', context)
        
    except Exception as e:
        logger.error(f"Erro inesperado ao excluir transação {transacao_id}: {str(e)}")
        messages.error(request, "Erro ao excluir a transação. Tente novamente.")
        return redirect('transacoes')
    return render(request, 'financas/test_filter.html')

@login_required
@require_http_methods(["POST"])
def gerar_parcelas_despesa(request, despesa_id):
    """Gera as parcelas de uma despesa parcelada."""
    try:
        despesa = get_object_or_404(DespesaParcelada.objects, id=despesa_id)
        
        if despesa.parcelas_geradas:
            messages.warning(request, "As parcelas desta despesa já foram geradas.")
        else:
            despesa.gerar_parcelas()
            messages.success(request, f"Parcelas geradas com sucesso! {despesa.numero_parcelas} parcelas foram criadas.")
        
    except Exception as e:
        messages.error(request, f"Erro ao gerar parcelas: {str(e)}")
    
    return redirect('detalhes_despesa_parcelada', despesa_id=despesa_id)


def home_view(request):
    """
    View para a página inicial que redireciona baseado no status de autenticação.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')
