from django import template

register = template.Library()

@register.inclusion_tag('financas/components/categoria_badge.html')
def categoria_badge(categoria_nome, categoria_cor=None, css_class=''):
    """
    Template tag para exibir badge de categoria de forma padronizada.
    
    Args:
        categoria_nome: Nome da categoria
        categoria_cor: Cor da categoria (opcional)
        css_class: Classes CSS adicionais (opcional)
    """
    return {
        'categoria_nome': categoria_nome,
        'categoria_cor': categoria_cor,
        'css_class': css_class
    }

@register.inclusion_tag('financas/components/categoria_badge.html')
def categoria_badge_obj(categoria, css_class=''):
    """
    Template tag para exibir badge de categoria usando objeto categoria.
    
    Args:
        categoria: Objeto categoria com atributos nome e cor
        css_class: Classes CSS adicionais (opcional)
    """
    return {
        'categoria_nome': categoria.nome if categoria else 'Sem categoria',
        'categoria_cor': categoria.cor if categoria else None,
        'css_class': css_class
    }