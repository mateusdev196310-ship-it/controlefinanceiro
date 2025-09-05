# Sistema de Logging Estruturado

Este documento descreve o sistema de logging estruturado implementado no projeto financeiro.

## Visão Geral

O sistema de logging estruturado foi implementado para fornecer:
- Logs em formato JSON para melhor análise
- Contexto automático de requisições (request ID, usuário, IP)
- Métricas de performance (duração de operações)
- Monitoramento de queries de banco de dados
- Categorização de logs por operação e tipo de entidade

## Componentes

### 1. Configuração de Logging (`financas/logging_config.py`)

#### StructuredFormatter
Formata logs em JSON com campos estruturados:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "financas.services",
  "message": "Conta criada com sucesso",
  "operation": "CREATE_CONTA",
  "entity_type": "Conta",
  "entity_id": 123,
  "duration_ms": 45,
  "request_id": "req_abc123",
  "user_id": 1
}
```

#### FinancasLoggerAdapter
Adiciona contexto automático aos logs:
- `request_id`: ID único da requisição
- `user_id`: ID do usuário autenticado
- `ip_address`: Endereço IP do cliente
- `user_agent`: User agent do navegador

### 2. Middleware de Logging (`financas/middleware.py`)

#### LoggingContextMiddleware
- Gera request_id único para cada requisição
- Adiciona contexto de usuário e requisição aos logs
- Configura thread-local storage para contexto global

#### DatabaseLoggingMiddleware
- Monitora número de queries por requisição
- Identifica queries lentas (> 100ms por padrão)
- Log de alertas para performance de banco de dados

### 3. Métodos de Logging Especializados

#### `log_operation()`
Para operações bem-sucedidas:
```python
logger.log_operation(
    level=logging.INFO,
    operation='CREATE_CONTA',
    entity_type='Conta',
    entity_id=conta.id,
    message='Conta criada com sucesso',
    duration_ms=45,
    nome=conta.nome,
    saldo_inicial=float(conta.saldo)
)
```

#### `log_error()`
Para erros e exceções:
```python
logger.log_error(
    operation='CREATE_CONTA',
    error=e,
    entity_type='Conta',
    error_code='VALIDATION_ERROR',
    nome=nome,
    saldo_inicial=saldo
)
```

#### `log_validation_error()`
Para erros de validação:
```python
logger.log_validation_error(
    operation='CREATE_CATEGORIA',
    field='nome',
    value=nome,
    error='Nome muito curto'
)
```

## Configuração

### Handlers Configurados

1. **Console Handler**
   - Nível: INFO
   - Formato: JSON estruturado
   - Saída: stdout

2. **File Handler**
   - Nível: DEBUG
   - Arquivo: `logs/financas.log`
   - Rotação: 10MB, 5 backups
   - Formato: JSON estruturado

3. **Error File Handler**
   - Nível: ERROR
   - Arquivo: `logs/financas_errors.log`
   - Rotação: 10MB, 5 backups
   - Apenas erros e exceções

### Configurações de Performance

No `settings.py`:
```python
LOGGING_PERFORMANCE = {
    'SLOW_QUERY_THRESHOLD_MS': 100,  # Queries > 100ms
    'HIGH_QUERY_COUNT_THRESHOLD': 10,  # Requests > 10 queries
    'LOG_ALL_QUERIES': False,  # Log todas as queries (dev)
}
```

## Uso nos Services

### Exemplo: ContaService

```python
from .logging_config import get_logger
import time
import logging

logger = get_logger(__name__)

def criar_conta(nome, saldo_inicial=None):
    start_time = time.time()
    
    try:
        # Lógica de criação...
        conta = Conta.objects.create(...)
        
        # Log de sucesso
        duration_ms = int((time.time() - start_time) * 1000)
        logger.log_operation(
            level=logging.INFO,
            operation='CREATE_CONTA',
            entity_type='Conta',
            entity_id=conta.id,
            message=f'Conta criada: {conta.nome}',
            duration_ms=duration_ms,
            nome=conta.nome,
            saldo_inicial=float(conta.saldo)
        )
        
        return conta
        
    except Exception as e:
        # Log de erro
        logger.log_error(
            operation='CREATE_CONTA',
            error=e,
            entity_type='Conta',
            error_code='CREATION_ERROR',
            nome=nome
        )
        raise
```

## Uso nas Views

### Exemplo: Validação com Logging

```python
from .logging_config import get_logger
import time
import logging

logger = get_logger(__name__)

def adicionar_categoria(request):
    if request.method == 'POST':
        start_time = time.time()
        nome = request.POST.get('nome', '').strip()
        
        # Validação com logging
        if not nome:
            logger.log_validation_error(
                operation='CREATE_CATEGORIA',
                field='nome',
                value='',
                error='Nome obrigatório'
            )
            messages.error(request, 'Nome é obrigatório')
            return render(request, 'form.html')
        
        try:
            categoria = Categoria.objects.create(nome=nome)
            
            # Log de sucesso
            duration_ms = int((time.time() - start_time) * 1000)
            logger.log_operation(
                level=logging.INFO,
                operation='CREATE_CATEGORIA',
                entity_type='Categoria',
                entity_id=categoria.id,
                message=f'Categoria criada: {categoria.nome}',
                duration_ms=duration_ms,
                nome=categoria.nome
            )
            
            return redirect('success')
            
        except Exception as e:
            logger.log_error(
                operation='CREATE_CATEGORIA',
                error=e,
                entity_type='Categoria',
                error_code='CREATION_ERROR',
                nome=nome
            )
            messages.error(request, 'Erro ao criar categoria')
            return render(request, 'form.html')
```

## Análise de Logs

### Estrutura dos Arquivos de Log

```
logs/
├── financas.log          # Todos os logs (DEBUG+)
├── financas_errors.log   # Apenas erros (ERROR+)
├── financas.log.1        # Backup rotacionado
└── financas_errors.log.1 # Backup de erros
```

### Exemplos de Queries para Análise

#### Operações mais lentas:
```bash
cat logs/financas.log | jq 'select(.duration_ms > 1000) | {operation, duration_ms, message}'
```

#### Erros por tipo:
```bash
cat logs/financas_errors.log | jq 'group_by(.error_code) | map({error_code: .[0].error_code, count: length})'
```

#### Operações por usuário:
```bash
cat logs/financas.log | jq 'select(.user_id) | group_by(.user_id) | map({user_id: .[0].user_id, operations: length})'
```

#### Performance de queries:
```bash
cat logs/financas.log | jq 'select(.query_count > 10) | {request_id, query_count, slow_queries}'
```

## Monitoramento

### Métricas Importantes

1. **Performance**
   - Duração média de operações
   - Queries lentas (> 100ms)
   - Requests com muitas queries (> 10)

2. **Erros**
   - Taxa de erro por operação
   - Tipos de erro mais comuns
   - Erros de validação por campo

3. **Uso**
   - Operações mais frequentes
   - Usuários mais ativos
   - Padrões de acesso

### Alertas Recomendados

- Query count > 15 por request
- Duração de operação > 2000ms
- Taxa de erro > 5% em 5 minutos
- Falhas de validação > 50% para um campo

## Boas Práticas

1. **Sempre medir duração** de operações importantes
2. **Usar códigos de erro** consistentes
3. **Incluir contexto relevante** nos logs
4. **Não logar informações sensíveis** (senhas, tokens)
5. **Usar níveis apropriados**:
   - DEBUG: Informações detalhadas de desenvolvimento
   - INFO: Operações normais bem-sucedidas
   - WARNING: Situações inesperadas mas não críticas
   - ERROR: Erros que impedem operações
   - CRITICAL: Falhas que podem afetar o sistema

## Troubleshooting

### Logs não aparecem
1. Verificar se middleware está configurado
2. Verificar permissões da pasta `logs/`
3. Verificar configuração de nível de log

### Performance degradada
1. Verificar se `LOG_ALL_QUERIES` está False em produção
2. Ajustar thresholds de performance
3. Considerar log assíncrono para alto volume

### Arquivos de log muito grandes
1. Verificar configuração de rotação
2. Ajustar tamanho máximo dos arquivos
3. Implementar limpeza automática de logs antigos