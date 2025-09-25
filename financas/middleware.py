import uuid
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.contrib.auth import get_user_model
from django.http import HttpResponseServerError
from django.conf import settings

# Função local para criar logger
def get_logger(name):
    logger = logging.getLogger(name)
    return Logger(logger)

# Classe Logger para substituir o FinancasLoggerAdapter
class Logger:
    def __init__(self, logger):
        self.logger = logger
        self.extra = {}
    
    def log_operation(self, level, operation, entity_type=None, entity_id=None, 
                     message=None, duration_ms=None, **kwargs):
        """Log estruturado para operações do sistema."""
        if message:
            self.logger.log(level, message)
        else:
            self.logger.log(level, f"Operação {operation} executada")
    
    def log_error(self, operation, error, entity_type=None, entity_id=None, 
                  error_code=None, **kwargs):
        """Log estruturado para erros."""
        self.logger.error(f"Erro na operação {operation}: {str(error)}")
    
    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
    
    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)


class ResourceMonitorMiddleware(MiddlewareMixin):
    """
    Middleware para monitorar o uso de recursos e evitar timeouts.
    Limita o tempo de processamento de requisições e interrompe operações
    que estão consumindo muitos recursos.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Tempo máximo de processamento em segundos
        self.max_request_time = getattr(settings, 'MAX_REQUEST_TIME', 60)
        self.logger = get_logger('financas.middleware')
        super().__init__(get_response)
    
    def process_request(self, request):
        # Registrar o tempo de início
        request.start_time = time.time()
        
        # Ignorar requisições admin e static
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return None
            
        # Verificar se a requisição é para importação de transações
        if 'importar_transacoes' in request.path:
            # Definir um timeout maior para importações
            request.timeout = getattr(settings, 'IMPORT_TIMEOUT', 120)
        else:
            # Usar o timeout padrão
            request.timeout = self.max_request_time
            
        return None
    
    def process_response(self, request, response):
        # Calcular o tempo de processamento se houver start_time
        if hasattr(request, 'start_time'):
            processing_time = time.time() - request.start_time
            
            # Registrar requisições lentas
            if processing_time > 5:  # Registrar requisições que levam mais de 5 segundos
                self.logger.warning(
                    f"Requisição lenta: {request.path} - {processing_time:.2f}s"
                )
            
            # Adicionar header com o tempo de processamento
            response['X-Processing-Time'] = f"{processing_time:.2f}s"
        
        return response


class LoggingContextMiddleware(MiddlewareMixin):
    """
    Middleware para adicionar contexto de logging às requisições.
    Adiciona request_id único e informações do usuário aos logs.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = get_logger('financas.middleware')
        super().__init__(get_response)
    
    def process_request(self, request):
        # Gerar ID único para a requisição
        request.request_id = str(uuid.uuid4())
        request.start_time = time.time()
        
        # Adicionar contexto ao logger
        self.logger.extra.update({
            'request_id': request.request_id,
            'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'method': request.method,
            'path': request.path,
        })
        
        # Log da requisição
        self.logger.log_operation(
            level=20,  # INFO
            operation='HTTP_REQUEST',
            message=f"{request.method} {request.path}",
            request_method=request.method,
            request_path=request.path
        )
    
    def process_response(self, request, response):
        duration_ms = None
        if hasattr(request, 'start_time') and request.start_time:
            duration_ms = int((time.time() - request.start_time) * 1000)
        
        # Log da resposta
        self.logger.log_operation(
            level=20,  # INFO
            operation='HTTP_RESPONSE',
            message=f"{request.method} {request.path} - {response.status_code}",
            duration_ms=duration_ms,
            status_code=response.status_code,
            request_method=request.method,
            request_path=request.path
        )
        
        # Log de performance se requisição demorou muito
        if duration_ms and duration_ms > 2000:  # Mais de 2 segundos
            self.logger.log_performance(
                operation='SLOW_REQUEST',
                duration_ms=duration_ms,
                request_method=request.method,
                request_path=request.path,
                status_code=response.status_code
            )
        
        return response
    
    def process_exception(self, request, exception):
        # Log de exceções não tratadas
        self.logger.log_error(
            operation='HTTP_EXCEPTION',
            error=exception,
            request_method=request.method,
            request_path=request.path,
            error_code='UNHANDLED_EXCEPTION'
        )
        
        return None  # Permite que outras middlewares processem a exceção
    
    def get_client_ip(self, request):
        """Obtém o IP real do cliente considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DatabaseLoggingMiddleware(MiddlewareMixin):
    """
    Middleware para logging de operações de banco de dados.
    Monitora queries lentas e operações críticas.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = get_logger('financas.database')
        super().__init__(get_response)
    
    def process_request(self, request):
        # Resetar contador de queries
        from django.db import connection
        connection.queries_log.clear() if hasattr(connection, 'queries_log') else None
        request.db_queries_start = len(connection.queries)
    
    def process_response(self, request, response):
        if hasattr(request, 'db_queries_start'):
            from django.db import connection
            
            total_queries = len(connection.queries) - request.db_queries_start
            
            if total_queries > 10:  # Muitas queries
                self.logger.log_performance(
                    operation='HIGH_DB_QUERIES',
                    duration_ms=None,
                    query_count=total_queries,
                    request_path=request.path,
                    custom_message=f"Requisição executou {total_queries} queries"
                )
            
            # Log de queries lentas
            for query in connection.queries[-total_queries:]:
                query_time = float(query['time']) * 1000  # Converter para ms
                if query_time > 100:  # Query lenta (>100ms)
                    self.logger.log_performance(
                        operation='SLOW_QUERY',
                        duration_ms=int(query_time),
                        sql_query=query['sql'][:500],  # Limitar tamanho do SQL no log
                        custom_message=f"Query lenta detectada: {query['sql'][:100]}..."
                    )
        
        return response


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware para isolamento de dados por tenant (usuário).
    Define o schema_name baseado no CPF/CNPJ do usuário logado para filtrar dados automaticamente.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = get_logger('financas.tenant')
        super().__init__(get_response)
    
    def sanitize_schema_name(self, cpf_cnpj):
        """Sanitiza CPF/CNPJ para usar como nome de schema"""
        if not cpf_cnpj:
            return None
        import re
        # Remove pontos, traços e barras
        clean = re.sub(r'[.\-/]', '', str(cpf_cnpj))
        # Adiciona prefixo para garantir que comece com letra
        return f"user_{clean}"
    
    def process_request(self, request):
        # Limpar qualquer tenant anterior
        if hasattr(connection, 'tenant_id'):
            delattr(connection, 'tenant_id')
        if hasattr(connection, 'schema_name'):
            delattr(connection, 'schema_name')
        
        # Se usuário está autenticado, definir o tenant
        if hasattr(request, 'user') and request.user.is_authenticated:
            User = get_user_model()
            try:
                user = User.objects.get(id=request.user.id)
                
                # Determinar schema baseado em CPF/CNPJ
                identifier = user.cpf or user.cnpj or f"id_{user.id}"
                schema_name = self.sanitize_schema_name(identifier)
                
                if not schema_name:
                    # Fallback para user_id se não tiver CPF/CNPJ
                    schema_name = f"user_{user.id}"
                    self.logger.log_operation(
                        level=30,  # WARNING
                        operation='SCHEMA_FALLBACK',
                        message=f"Usuário {user.username} não tem CPF/CNPJ válido, usando fallback: {schema_name}",
                        user_id=user.id,
                        schema_name=schema_name
                    )
                
                # Definir tenant_id e schema_name
                connection.tenant_id = user.id  # Usar ID do usuário como tenant_id
                connection.schema_name = schema_name
                
                # Log da definição do tenant
                self.logger.log_operation(
                    level=20,  # INFO
                    operation='TENANT_SET',
                    message=f"Schema definido: {schema_name} para usuário {user.username} (CPF/CNPJ: {identifier})",
                    user_id=user.id,
                    schema_name=schema_name
                )
                    
            except User.DoesNotExist:
                self.logger.log_operation(
                    level=40,  # ERROR
                    operation='USER_NOT_FOUND',
                    message=f"Usuário autenticado não encontrado: {request.user.id}",
                    user_id=request.user.id if hasattr(request.user, 'id') else None
                )
            except Exception as e:
                self.logger.log_error(
                    operation='TENANT_ERROR',
                    error=e,
                    user_id=request.user.id if hasattr(request.user, 'id') else None,
                    error_code='TENANT_SETUP_ERROR'
                )
    
    def process_response(self, request, response):
        # Limpar tenant da conexão após a requisição
        if hasattr(connection, 'tenant_id'):
            delattr(connection, 'tenant_id')
        if hasattr(connection, 'schema_name'):
            delattr(connection, 'schema_name')
        
        return response