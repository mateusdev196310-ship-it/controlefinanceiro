"""Exceções customizadas para a aplicação financas.

Este módulo define exceções específicas do domínio da aplicação,
facilitando o tratamento de erros e a depuração.
"""

class FinancasBaseException(Exception):
    """Exceção base para todas as exceções da aplicação financas."""
    
    def __init__(self, message, code=None, details=None):
        """
        Inicializa a exceção base.
        
        Args:
            message (str): Mensagem de erro
            code (str, optional): Código do erro para identificação
            details (dict, optional): Detalhes adicionais do erro
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"
    
    def to_dict(self):
        """Converte a exceção para um dicionário para serialização."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'code': self.code,
            'details': self.details
        }

class ContaServiceError(FinancasBaseException):
    """Exceção para erros relacionados ao serviço de contas."""
    pass

class TransacaoServiceError(FinancasBaseException):
    """Exceção para erros relacionados ao serviço de transações."""
    pass

class ValidationError(FinancasBaseException):
    """Exceção para erros de validação de dados."""
    pass

class BusinessRuleError(FinancasBaseException):
    """Exceção para violações de regras de negócio."""
    pass

class DataIntegrityError(FinancasBaseException):
    """Exceção para erros de integridade de dados."""
    pass

class PermissionError(FinancasBaseException):
    """Exceção para erros de permissão/autorização."""
    pass

class ConfigurationError(FinancasBaseException):
    """Exceção para erros de configuração da aplicação."""
    pass