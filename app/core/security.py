"""
Middlewares e utilitários de segurança
"""
import time
import re
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import SECURITY_CONFIG

# Cache para verificar se a aplicação está inicializada
app_initialized = False
initialization_time = None

# Contador de tentativas de ataque por IP
attack_attempts = defaultdict(int)

# Lista de IPs bloqueados
BLOCKED_IPS = set()


def mark_app_as_initialized():
    """Marca a aplicação como inicializada"""
    global app_initialized, initialization_time
    app_initialized = True
    initialization_time = time.time()
    print(f"✅ Aplicação marcada como inicializada em {initialization_time}")


def is_app_ready():
    """Verifica se a aplicação está pronta para receber requests"""
    return app_initialized and (time.time() - initialization_time) > SECURITY_CONFIG['initialization_buffer']


class AttackPatterns:
    """Detector de padrões de ataque"""
    MALICIOUS_PATTERNS = [
        r'\.\./',  # Path traversal
        r'\.\.\\',  # Path traversal Windows
        r'usr/local/lib',  # Sistema de arquivos
        r'/tmp/',  # Diretório temporário
        r'/etc/',  # Arquivos de sistema
        r'think\\app',  # ThinkPHP vulnerabilities
        r'invokefunction',  # Function injection
        r'call_user_func',  # PHP function calls
        r'<?php',  # PHP injection
        r'wp-admin',  # WordPress attacks
        r'phpmyadmin',  # Database admin attacks
        r'config\.php',  # Config file access
        r'index\.php',  # PHP file access
    ]
    
    @classmethod
    def is_malicious(cls, url: str, user_agent: str = "") -> bool:
        text_to_check = f"{url} {user_agent}".lower()
        
        for pattern in cls.MALICIOUS_PATTERNS:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                return True
        return False


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware de segurança para proteção contra ataques"""
    
    def __init__(self, app):
        super().__init__(app)
        self.startup_time = time.time()
        self.warmup_period = SECURITY_CONFIG['warmup_period']

    async def dispatch(self, request: Request, call_next):
        try:
            # Durante o período de warmup, ser menos restritivo
            is_warmup = (time.time() - self.startup_time) < self.warmup_period
            app_ready = is_app_ready()

            # Permitir mais rotas durante startup/warmup
            allowed_during_startup = ["/", "/health", "/docs", "/openapi.json", "/redoc"]
            
            # Se a aplicação não está pronta, permitir health checks e docs
            if not app_ready and request.url.path not in allowed_during_startup:
                if not is_warmup:  # Só bloqueia após warmup
                    return JSONResponse(
                        status_code=503,
                        content={"error": "Service temporarily unavailable", "message": "Application is starting up"}
                    )

            # Obter IP real
            client_ip = self.get_real_ip(request)

            # Verificar IP bloqueado (apenas após warmup)
            if not is_warmup and client_ip in BLOCKED_IPS:
                return JSONResponse(
                    status_code=403,
                    content={"error": "IP blocked"}
                )

            # Verificar padrões de ataque (apenas após warmup)
            if not is_warmup:
                url = str(request.url)
                user_agent = request.headers.get("user-agent", "")

                if AttackPatterns.is_malicious(url, user_agent):
                    print(f"🚨 ATAQUE DETECTADO de {client_ip}: {url}")

                    # Incrementar contador de ataques
                    attack_attempts[client_ip] += 1

                    # Bloquear IP após N tentativas
                    if attack_attempts[client_ip] >= SECURITY_CONFIG['max_attack_attempts']:
                        BLOCKED_IPS.add(client_ip)
                        print(f"🚫 IP {client_ip} BLOQUEADO após {attack_attempts[client_ip]} ataques")

                    return JSONResponse(
                        status_code=403,
                        content={"error": "Malicious request detected"}
                    )

            # Verificar rotas permitidas (mais permissivo durante warmup)
            if not is_warmup and not self.is_allowed_path(request.url.path):
                return JSONResponse(
                    status_code=404,
                    content={"error": "Not found"}
                )

            # Continuar com a requisição normal
            return await call_next(request)

        except Exception as e:
            print(f"❌ Erro no middleware de segurança: {e}")
            # Em caso de erro no middleware, permitir a requisição
            return await call_next(request)
    
    def get_real_ip(self, request: Request) -> str:
        """Obtém o IP real do cliente considerando proxies"""
        for header in ["x-real-ip", "x-forwarded-for"]:
            ip = request.headers.get(header)
            if ip:
                return ip.split(',')[0].strip()
        
        return getattr(request.client, 'host', 'unknown')
    
    def is_allowed_path(self, path: str) -> bool:
        """Verifica se o path é permitido"""
        allowed_patterns = [
            r'^/api_operacao/avaliare_db_pearson_2025/',  # ✅ COMPATIBILIDADE: URL antiga (frontend)
            r'^/api_operacao/',      # Rotas da API (genérico)
            r'^/apiavrede/',         # Rotas legacy
            r'^/import/',            # Rotas de importação
            r'^/estrutura/',         # Rotas de estrutura
            r'^/docs',               # FastAPI docs
            r'^/redoc',              # ReDoc
            r'^/openapi.json',       # OpenAPI spec
            r'^/$',                  # Root
            r'^/favicon.ico',        # Favicon
            r'^/health',             # Health check
            r'^/security/',          # Endpoints de segurança
            r'^/test',               # Endpoint de teste
        ]

        for pattern in allowed_patterns:
            if re.match(pattern, path):
                return True

        print(f"❌ Path bloqueado: {path}")
        return False

