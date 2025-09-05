"""Constantes centralizadas para a aplicação financas.

Este módulo contém todas as constantes utilizadas na aplicação,
evitando valores mágicos espalhados pelo código e facilitando a manutenção.
"""

# Tipos de transação
class TipoTransacao:
    """Constantes para tipos de transação."""
    RECEITA = 'receita'
    DESPESA = 'despesa'
    SAIDA = 'saida'  # Para parcelas e outras saídas
    
    CHOICES = [
        (RECEITA, 'Receita'),
        (DESPESA, 'Despesa'),
        (SAIDA, 'Saída'),
    ]
    
    @classmethod
    def get_all_types(cls):
        """Retorna todos os tipos de transação disponíveis."""
        return [cls.RECEITA, cls.DESPESA, cls.SAIDA]
    
    @classmethod
    def get_expense_types(cls):
        """Retorna todos os tipos que representam despesas/saídas."""
        return [cls.DESPESA, cls.SAIDA]
    
    @classmethod
    def is_valid_type(cls, tipo):
        """Verifica se o tipo de transação é válido."""
        return tipo in cls.get_all_types()
    
    @classmethod
    def is_expense_type(cls, tipo):
        """Verifica se o tipo representa uma despesa/saída."""
        return tipo in cls.get_expense_types()

# Configurações de formatação
class FormatConfig:
    """Constantes para formatação de valores e datas."""
    DECIMAL_PLACES = 2
    MAX_DIGITS = 10
    CURRENCY_SYMBOL = 'R$'
    DATE_FORMAT = '%d/%m/%Y'
    DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'

# Mensagens de erro padronizadas
class ErrorMessages:
    """Mensagens de erro padronizadas para a aplicação."""
    VALOR_NEGATIVO = 'O valor não pode ser negativo.'
    VALOR_ZERO = 'O valor deve ser maior que zero.'
    CONTA_INEXISTENTE = 'A conta especificada não existe.'
    TRANSACAO_INEXISTENTE = 'A transação especificada não existe.'
    TIPO_INVALIDO = 'Tipo de transação inválido.'
    DATA_FUTURA = 'A data não pode ser no futuro.'
    DESCRICAO_VAZIA = 'A descrição não pode estar vazia.'
    SALDO_INSUFICIENTE = 'Saldo insuficiente para esta operação.'
    
# Mensagens de sucesso padronizadas
class SuccessMessages:
    """Mensagens de sucesso padronizadas para a aplicação."""
    TRANSACAO_CRIADA = 'Transação criada com sucesso.'
    TRANSACAO_ATUALIZADA = 'Transação atualizada com sucesso.'
    TRANSACAO_DELETADA = 'Transação deletada com sucesso.'
    TRANSACAO_EXCLUIDA = 'Transação excluída com sucesso.'
    CONTA_CRIADA = 'Conta criada com sucesso.'
    CONTA_ATUALIZADA = 'Conta atualizada com sucesso.'
    SALDO_ATUALIZADO = 'Saldo atualizado com sucesso.'

# Configurações de paginação
class PaginationConfig:
    """Configurações para paginação de listas."""
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    
# Configurações de validação
class ValidationConfig:
    """Configurações para validações."""
    MAX_DESCRICAO_LENGTH = 200
    MAX_NOME_CONTA_LENGTH = 100
    MIN_DESCRICAO_LENGTH = 3
    MIN_NOME_CONTA_LENGTH = 2
    
# Status de operações
class OperationStatus:
    """Status de operações do sistema."""
    SUCCESS = 'success'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'
    
    CHOICES = [
        (SUCCESS, 'Sucesso'),
        (ERROR, 'Erro'),
        (WARNING, 'Aviso'),
        (INFO, 'Informação'),
    ]

# Configurações de logging
class LogConfig:
    """Configurações para logging estruturado."""
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Níveis de log
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'