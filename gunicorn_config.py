# gunicorn_config.py
import os
import multiprocessing

# Configuração otimizada para resolver intermitência 503

# Bind - onde o servidor irá rodar
bind = "0.0.0.0:8000"

# Workers - AUMENTADO para melhor performance
workers = int(os.getenv("WORKERS", 4))  # Aumentado de 2 para 4 workers
worker_class = "uvicorn.workers.UvicornWorker"

# Conexões por worker
worker_connections = 1000

# Timeouts - OTIMIZADOS para evitar 503
timeout = 120  # Aumentado de 30 para 120 segundos
keepalive = 5
graceful_timeout = 30

# Restart workers - IMPORTANTE para estabilidade
max_requests = 1000  # Worker restarta após 1000 requests
max_requests_jitter = 100  # Adiciona variação aleatória

# Preload - MELHORA startup time
preload_app = True

# Memory management
worker_tmp_dir = "/dev/shm"  # Usa RAM para temporary files

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Performance tuning
backlog = 2048
