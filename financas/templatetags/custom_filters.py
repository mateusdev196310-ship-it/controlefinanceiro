from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Retorna um item de um dicionário pelo índice"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    elif isinstance(dictionary, list) and key < len(dictionary):
        return dictionary[key]
    return None

@register.filter
def absolute(value):
    """Retorna o valor absoluto de um número"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value