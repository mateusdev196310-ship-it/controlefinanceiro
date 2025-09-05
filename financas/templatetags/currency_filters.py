from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def currency_br(value):
    """
    Formata um valor monetário no padrão brasileiro: R$ 1.234,56
    Trata corretamente valores negativos: -R$ 1.234,56
    """
    if value is None or value == '':
        return "R$ 0,00"
    
    try:
        # Converte para Decimal para garantir precisão
        if isinstance(value, str):
            # Remove espaços e verifica se é uma string vazia
            value = value.strip()
            if not value:
                return "R$ 0,00"
            # Tenta converter string para decimal
            value = Decimal(value)
        elif isinstance(value, (int, float)):
            value = Decimal(str(value))
        elif not isinstance(value, Decimal):
            # Tenta converter qualquer outro tipo para string primeiro
            str_value = str(value)
            value = Decimal(str_value)
        
        # Verifica se é negativo
        is_negative = value < 0
        
        # Trabalha com valor absoluto para formatação
        abs_value = abs(value)
        
        # Formata o valor
        formatted = f"{abs_value:.2f}"
        
        # Separa parte inteira e decimal
        integer_part, decimal_part = formatted.split('.')
        
        # Adiciona separadores de milhares
        if len(integer_part) > 3:
            # Inverte a string, adiciona pontos a cada 3 dígitos, depois inverte novamente
            reversed_int = integer_part[::-1]
            grouped = '.'.join([reversed_int[i:i+3] for i in range(0, len(reversed_int), 3)])
            integer_part = grouped[::-1]
        
        # Monta o resultado final com sinal correto
        if is_negative:
            return f"-R$ {integer_part},{decimal_part}"
        else:
            return f"R$ {integer_part},{decimal_part}"
    
    except Exception as e:
        return "R$ 0,00"