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

