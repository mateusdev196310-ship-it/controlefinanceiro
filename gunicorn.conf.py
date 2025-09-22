# Gunicorn configuration file
import multiprocessing

# Número de workers - recomendado: (2 x núcleos) + 1
# No Render Free Tier, temos recursos limitados, então usamos menos workers
workers = 2

# Tipo de worker - usar gevent para melhor desempenho com I/O bound
worker_class = 'gevent'

# Timeout aumentado para operações longas (em segundos)
timeout = 120

# Keepalive para conexões persistentes (em segundos)
keepalive = 5

# Número máximo de requisições por worker antes de reiniciar
max_requests = 1000
max_requests_jitter = 50

# Configurações de log
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Configurações de performance
worker_connections = 1000

# Configurações para evitar memory leaks
preload_app = True