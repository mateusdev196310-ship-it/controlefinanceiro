import logging
import logging.config
from datetime import datetime
import json
from django.conf import settings


class StructuredFormatter(logging.Formatter):
    """
    Formatter personalizado para logs estruturados em JSON.
    """
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Adicionar informações extras se disponíveis
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        
        if hasattr(record, 'entity_type'):
            log_entry['entity_type'] = record.entity_type
        
        if hasattr(record, 'entity_id'):
            log_entry['entity_id'] = record.entity_id
        
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        
        if hasattr(record, 'error_code'):
            log_entry['error_code'] = record.error_code
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        # Adicionar informações de exceção se presente
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False)


class FinancasLoggerAdapter(logging.LoggerAdapter):
    """
    Adapter para adicionar contexto específico do sistema financeiro aos logs.
    """
    
    def __init__(self, logger, extra=None):
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        # Adicionar informações extras do contexto
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        kwargs['extra'].update(self.extra)
        return msg, kwargs
    
    def log_operation(self, level, operation, entity_type=None, entity_id=None, 
                     message=None, duration_ms=None, **kwargs):
        """
        Log estruturado para operações do sistema.
        
        Args:
            level: Nível do log (INFO, ERROR, etc.)
            operation: Nome da operação (CREATE_TRANSACTION, UPDATE_ACCOUNT, etc.)
            entity_type: Tipo da entidade (Transacao, Conta, etc.)
            entity_id: ID da entidade
            message: Mensagem adicional
            duration_ms: Duração da operação em milissegundos
        """
        extra = {
            'operation': operation,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'duration_ms': duration_ms,
        }
        
        # Adicionar kwargs extras
        extra.update(kwargs)
        
        # Filtrar valores None
        extra = {k: v for k, v in extra.items() if v is not None}
        
        self.log(level, message or f"Operação {operation} executada", extra=extra)
    
    def log_error(self, operation, error, entity_type=None, entity_id=None, 
                  error_code=None, **kwargs):
        """
        Log estruturado para erros.
        """
        extra = {
            'operation': operation,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'error_code': error_code,
        }
        
        extra.update(kwargs)
        extra = {k: v for k, v in extra.items() if v is not None}
        
        self.error(f"Erro na operação {operation}: {str(error)}", extra=extra, exc_info=True)
    
    def log_performance(self, operation, duration_ms, entity_type=None, 
                       entity_id=None, **kwargs):
        """
        Log estruturado para métricas de performance.
        """
        level = logging.WARNING if duration_ms and duration_ms > 1000 else logging.INFO
        
        self.log_operation(
            level=level,
            operation=operation,
            entity_type=entity_type,
            entity_id=entity_id,
            duration_ms=duration_ms,
            message=f"Operação {operation} executada em {duration_ms}ms",
            **kwargs
        )


# Configuração de logging estruturado
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structured': {
            '()': 'financas.logging_config.StructuredFormatter',
        },
        'simple': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO',
        },
        'file_structured': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/financas_structured.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'structured',
            'level': 'INFO',
        },
        'file_errors': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/financas_errors.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'structured',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'financas': {
            'handlers': ['console', 'file_structured', 'file_errors'],
            'level': 'INFO',
            'propagate': False,
        },
        'financas.services': {
            'handlers': ['file_structured', 'file_errors'],
            'level': 'INFO',
            'propagate': False,
        },
        'financas.models': {
            'handlers': ['file_structured', 'file_errors'],
            'level': 'INFO',
            'propagate': False,
        },
        'financas.views': {
            'handlers': ['console', 'file_structured', 'file_errors'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


def get_logger(name):
    """
    Retorna um logger estruturado para o módulo especificado.
    
    Args:
        name: Nome do módulo/logger
        
    Returns:
        FinancasLoggerAdapter: Logger com funcionalidades estruturadas
    """
    logger = logging.getLogger(name)
    return FinancasLoggerAdapter(logger)


def setup_logging():
    """
    Configura o sistema de logging estruturado.
    Deve ser chamado na inicialização da aplicação.
    """
    import os
    
    # Criar diretório de logs se não existir
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Aplicar configuração
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Log de inicialização
    logger = get_logger('financas.logging')
    logger.info("Sistema de logging estruturado inicializado")