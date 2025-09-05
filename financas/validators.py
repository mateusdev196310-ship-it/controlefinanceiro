from django.core.exceptions import ValidationError
import re
import requests
from typing import Optional

def validar_senha_forte(senha: str) -> bool:
    """
    Valida se uma senha atende aos critérios de segurança.
    
    Critérios:
    - Pelo menos 8 caracteres
    - Pelo menos uma letra minúscula
    - Pelo menos uma letra maiúscula
    - Pelo menos um número
    - Pelo menos um caractere especial
    
    Args:
        senha: String contendo a senha a ser validada
        
    Returns:
        bool: True se a senha for forte, False caso contrário
    """
    if len(senha) < 8:
        return False
    
    # Verifica se tem pelo menos uma letra minúscula
    if not re.search(r'[a-z]', senha):
        return False
    
    # Verifica se tem pelo menos uma letra maiúscula
    if not re.search(r'[A-Z]', senha):
        return False
    
    # Verifica se tem pelo menos um número
    if not re.search(r'\d', senha):
        return False
    
    # Verifica se tem pelo menos um caractere especial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        return False
    
    return True

def django_validar_senha_forte(value: str) -> None:
    """
    Validator para uso em campos do Django.
    
    Args:
        value: Valor da senha a ser validada
        
    Raises:
        ValidationError: Se a senha não for forte o suficiente
    """
    if not validar_senha_forte(value):
        raise ValidationError(
            'A senha deve ter pelo menos 8 caracteres, incluindo: '
            'uma letra minúscula, uma maiúscula, um número e um caractere especial.'
        )

def validar_cpf(cpf: str) -> bool:
    """
    Valida um número de CPF brasileiro.
    
    Args:
        cpf: String contendo o CPF a ser validado
        
    Returns:
        bool: True se o CPF for válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cpf = re.sub(r'\D', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula o primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    # Verifica o primeiro dígito
    if int(cpf[9]) != digito1:
        return False
    
    # Calcula o segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    # Verifica o segundo dígito
    return int(cpf[10]) == digito2

def validar_cnpj(cnpj: str) -> bool:
    """
    Valida um número de CNPJ brasileiro.
    
    Args:
        cnpj: String contendo o CNPJ a ser validado
        
    Returns:
        bool: True se o CNPJ for válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cnpj = re.sub(r'\D', '', cnpj)
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Calcula o primeiro dígito verificador
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    # Verifica o primeiro dígito
    if int(cnpj[12]) != digito1:
        return False
    
    # Calcula o segundo dígito verificador
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    # Verifica o segundo dígito
    return int(cnpj[13]) == digito2

def django_validar_cpf(value: str) -> None:
    """
    Validator para uso em campos do Django.
    
    Args:
        value: Valor do CPF a ser validado
        
    Raises:
        ValidationError: Se o CPF for inválido
    """
    if not validar_cpf(value):
        raise ValidationError('CPF inválido.')

def django_validar_cnpj(value: str) -> None:
    """
    Validator para uso em campos do Django.
    
    Args:
        value: Valor do CNPJ a ser validado
        
    Raises:
        ValidationError: Se o CNPJ for inválido
    """
    if not validar_cnpj(value):
        raise ValidationError('CNPJ inválido.')

def formatar_cpf(cpf: str) -> str:
    """
    Formata um CPF para exibição.
    
    Args:
        cpf: CPF sem formatação
        
    Returns:
        str: CPF formatado (XXX.XXX.XXX-XX)
    """
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) == 11:
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    return cpf

def formatar_cnpj(cnpj: str) -> str:
    """
    Formata um CNPJ para exibição.
    
    Args:
        cnpj: CNPJ sem formatação
        
    Returns:
        str: CNPJ formatado (XX.XXX.XXX/XXXX-XX)
    """
    cnpj = re.sub(r'\D', '', cnpj)
    if len(cnpj) == 14:
        return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'
    return cnpj

def buscar_dados_cnpj(cnpj: str) -> Optional[dict]:
    """
    Busca dados de uma empresa na API da Receita Federal.
    
    Args:
        cnpj: CNPJ da empresa (com ou sem formatação)
        
    Returns:
        dict: Dados da empresa ou None se não encontrado
    """
    try:
        # Remove formatação
        cnpj_limpo = re.sub(r'\D', '', cnpj)
        
        # Valida o CNPJ antes de fazer a consulta
        if not validar_cnpj(cnpj_limpo):
            return None
        
        # URL da API pública da Receita Federal
        url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}'
        
        # Faz a requisição
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            # Verifica se a consulta foi bem-sucedida
            if dados.get('status') == 'OK':
                return {
                    'razao_social': dados.get('nome', ''),
                    'nome_fantasia': dados.get('fantasia', ''),
                    'cnpj': dados.get('cnpj', ''),
                    'situacao': dados.get('situacao', ''),
                    'endereco': {
                        'logradouro': dados.get('logradouro', ''),
                        'numero': dados.get('numero', ''),
                        'complemento': dados.get('complemento', ''),
                        'bairro': dados.get('bairro', ''),
                        'municipio': dados.get('municipio', ''),
                        'uf': dados.get('uf', ''),
                        'cep': dados.get('cep', ''),
                    },
                    'telefone': dados.get('telefone', ''),
                    'email': dados.get('email', ''),
                    'atividade_principal': dados.get('atividade_principal', []),
                    'data_situacao': dados.get('data_situacao', ''),
                    'tipo': dados.get('tipo', ''),
                    'porte': dados.get('porte', ''),
                }
        
        return None
        
    except requests.RequestException:
        # Em caso de erro na requisição, retorna None
        return None
    except Exception:
        # Em caso de qualquer outro erro, retorna None
        return None