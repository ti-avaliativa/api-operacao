"""
Configurações centralizadas da aplicação
"""
import os
from typing import Set

# Configuração da API Key
VALID_API_KEY = os.getenv("API_KEY")

# Validação: garantir que a API_KEY foi definida
if not VALID_API_KEY:
    raise ValueError("❌ API_KEY não foi definida nas variáveis de ambiente")

print(f"✅ API_KEY carregada: {VALID_API_KEY[:20]}..." if VALID_API_KEY else "❌ API_KEY não encontrada")

# Rotas que não precisam de autenticação
EXCLUDED_PATHS: Set[str] = {   
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
    "/"
}

# Padrões de rotas que não precisam de autenticação (regex)
EXCLUDED_PATTERNS = [
    r"^/[^/]+$",  # Padrão /{db} - rota básica de validação
    r"^/import/info$",  # Endpoint de informações de importação
]

# Configurações do banco de dados
# IMPORTANTE: NÃO especificamos 'database' aqui!
# O banco é selecionado via comando USE {db} em cada query
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "3306")),  # Porta pode ter padrão
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    # database NÃO é especificado - será selecionado via USE {db}
}

# Validar configurações obrigatórias do banco de dados
if not DB_CONFIG["host"]:
    raise ValueError("❌ DB_HOST não foi definida no arquivo .env")
if not DB_CONFIG["user"]:
    raise ValueError("❌ DB_USER não foi definido no arquivo .env")
if DB_CONFIG["password"] is None:
    raise ValueError("❌ DB_PASSWORD não foi definida no arquivo .env")

print(f"✅ Banco de dados configurado: {DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")

# Configurações do pool de conexões
POOL_CONFIG = {
    "pool_name": "my_pool",
    "pool_size": 10,
    "pool_reset_session": True,
    "autocommit": True,
    "connection_timeout": 30,  # Aumentado para 30 segundos
    "buffered": True,
    "compress": False,  # DESABILITADO: compress=True pode causar erro "unpack requires a buffer of 4 bytes"
    "charset": 'utf8mb4',
    "collation": 'utf8mb4_general_ci',
    "use_unicode": True,
    "get_warnings": True,
    "raise_on_warnings": False,
    "read_timeout": 300,  # 5 minutos
    "write_timeout": 300  # 5 minutos
}

# Configurações de cache
CACHE_CONFIG = {
    "default_ttl": 10,
    "default_maxsize": 100
}

# Configurações de segurança
SECURITY_CONFIG = {
    "warmup_period": 10,  # segundos
    "max_attack_attempts": 3,
    "initialization_buffer": 5  # segundos
}

# Configurações de importação
IMPORT_CONFIG = {
    "max_file_size": 25 * 1024 * 1024,  # 25MB
    "allowed_extensions": ['.csv'],
    "csv_preview_rows": 5
}

