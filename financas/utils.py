from decimal import Decimal, InvalidOperation
import re
from django.utils import timezone
import pytz
from functools import lru_cache
from datetime import datetime, timedelta

# Cache do fuso horário para melhor performance
@lru_cache(maxsize=1)
def _get_fuso_brasil():
    """Retorna o fuso horário do Brasil com cache para performance."""
    return pytz.timezone('America/Sao_Paulo')

def get_data_atual_brasil():
    """
    Obtém a data atual no fuso horário do Brasil (America/Sao_Paulo).
    
    Esta função centraliza a lógica de obtenção da data atual considerando
    o fuso horário brasileiro, incluindo horário de verão automático.
    
    Returns:
        date: Data atual no fuso horário do Brasil
    
    Performance:
        - Usa cache para o fuso horário (lru_cache)
        - Evita recriação desnecessária do objeto timezone
    """
    fuso_brasil = _get_fuso_brasil()
    return timezone.localtime(timezone.now(), fuso_brasil).date()

def validar_data_futura(data):
    """
    Valida se uma data não é futura considerando o fuso horário do Brasil.
    
    Args:
        data (date): Data a ser validada
        
    Returns:
        bool: True se a data é futura, False caso contrário
        
    Raises:
        None: Função não levanta exceções
    """
    if not data:
        return False
    
    hoje_brasil = get_data_atual_brasil()
    return data > hoje_brasil

def parse_currency_value(value_str):
    """
    Converte uma string de valor monetário formatado (ex: "1.234,56") para Decimal.
    
    Args:
        value_str (str): String com valor formatado no padrão brasileiro
        
    Returns:
        Decimal: Valor convertido para Decimal
        
    Raises:
        ValueError: Se o valor não puder ser convertido
    """
    if not value_str:
        return Decimal('0.00')
    
    # Remove espaços em branco
    value_str = str(value_str).strip()
    
    # Se já é um número válido (sem formatação), converte diretamente
    try:
        return Decimal(value_str)
    except InvalidOperation:
        pass
    
    # Remove caracteres não numéricos exceto vírgula e ponto
    clean_value = re.sub(r'[^\d,.]', '', value_str)
    
    # Se não há vírgula nem ponto, assume que são centavos
    if ',' not in clean_value and '.' not in clean_value:
        if clean_value:
            return Decimal(clean_value) / 100
        return Decimal('0.00')
    
    # Se há vírgula, assume formato brasileiro (vírgula = decimal, ponto = milhares)
    if ',' in clean_value:
        # Remove pontos (separadores de milhares) e substitui vírgula por ponto
        clean_value = clean_value.replace('.', '').replace(',', '.')
    
    try:
        return Decimal(clean_value)
    except InvalidOperation:
        raise ValueError(f"Valor inválido: {value_str}")

def verificar_mes_fechado(data, conta):
    """
    Verifica se uma data está em um mês que foi fechado para uma conta específica.
    
    Args:
        data (date): Data a ser verificada
        conta (Conta): Conta para verificar o fechamento
        
    Returns:
        tuple: (bool, str) - (está_fechado, mensagem)
    """
    from .models import FechamentoMensal
    
    try:
        # Busca fechamento para o ano/mês da data
        fechamento = FechamentoMensal.objects.filter(
            conta=conta,
            ano=data.year,
            mes=data.month,
            fechado=True
        ).first()
        
        if fechamento:
            return True, f"Mês {data.month}/{data.year} está fechado para a conta {conta.nome}"
        
        return False, "Mês não está fechado"
        
    except Exception as e:
        return False, f"Erro ao verificar fechamento: {str(e)}"

def pode_editar_transacao(transacao):
    """
    Verifica se uma transação pode ser editada ou excluída.
    
    Args:
        transacao (Transacao): Transação a ser verificada
        
    Returns:
        tuple: (bool, str) - (pode_editar, mensagem)
    """
    esta_fechado, mensagem = verificar_mes_fechado(transacao.data, transacao.conta)
    
    if esta_fechado:
        return False, f"Não é possível editar/excluir transação: {mensagem}"
    
    return True, "Transação pode ser editada"

def format_currency_br(value):
    """
    Formata um valor Decimal para o padrão brasileiro.
    Trata corretamente valores negativos.
    
    Args:
        value (Decimal): Valor a ser formatado
        
    Returns:
        str: Valor formatado (ex: "1.234,56" ou "-1.234,56")
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # Verifica se é negativo
    is_negative = value < 0
    
    # Trabalha com valor absoluto para formatação
    abs_value = abs(value)
    
    # Formata o valor
    formatted = f"{abs_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # Adiciona sinal negativo se necessário
    if is_negative:
        return f"-{formatted}"
    else:
        return formatted