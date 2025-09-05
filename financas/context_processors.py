# -*- coding: utf-8 -*-
"""
Context processors para o sistema financeiro.
Fornece dados globais para todos os templates.
"""

def company_info(request):
    """
    Fornece informações da empresa para todos os templates.
    Facilita a manutenção das informações do cabeçalho.
    """
    return {
        'COMPANY_INFO': {
            'name': 'Sistema Financeiro',
            'logo_icon': 'fas fa-building',
            'phone': '(73) 98238-3397',
            'email': 'mateusqa.testes@gmail.com',
            'website': 'www.financeiro.com',
            'description': 'Sistema de Controle Financeiro'
        }
    }

def system_info(request):
    """
    Fornece informações do sistema para todos os templates.
    """
    return {
        'SYSTEM_INFO': {
            'version': '1.0.0',
            'name': 'Sistema Financeiro',
            'support_email': 'suporte@financeirotech.com'
        }
    }