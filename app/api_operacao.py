"""
API de Operações - Avaliare
Arquivo principal da aplicação FastAPI
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import re

# Importações dos módulos core
from app.core.config import VALID_API_KEY, EXCLUDED_PATHS, EXCLUDED_PATTERNS
from app.core.security import SecurityMiddleware, mark_app_as_initialized

# Importações dos routers
from app.routers import estrutura, alunos, sistema

# Criar aplicação FastAPI
app = FastAPI(
    root_path="/apiavrede",
    title="API de Operações - Avaliare",
    description="API para importação de alunos e gerenciamento de estrutura organizacional",
    version="2.0.0"
)

# ========================================
# MIDDLEWARE: Extração do Nome do Banco (OPCIONAL)
# ========================================
# NOTA: Este middleware foi DESABILITADO para seguir o padrão do código legado
# Agora as rotas aceitam {db} como parâmetro de path diretamente
# Formato: /{db}/endpoint (exemplo: /avaliare_db_pearson_2025/import/completo)
# 
# O código anterior esperava /api_operacao/{db}/endpoint, mas com root_path="/apiavrede"
# isso causava conflitos. Agora seguimos o padrão simples /{db}/endpoint


# ========================================
# MIDDLEWARE: Validação de API Key
# ========================================
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """
    Middleware para validar API key em todas as rotas exceto as excluídas
    """
    # Verificar se a rota está na lista de exclusões
    path_without_root = request.url.path
    if app.root_path and path_without_root.startswith(app.root_path):
        path_without_root = path_without_root[len(app.root_path):]
    
    # Verificar rotas exatas
    if path_without_root in EXCLUDED_PATHS:
        response = await call_next(request)
        return response
    
    # Verificar padrões de rotas (regex)
    for pattern in EXCLUDED_PATTERNS:
        if re.match(pattern, path_without_root):
            print(f"✅ Rota {path_without_root} excluída por padrão: {pattern}")
            response = await call_next(request)
            return response
    
    # Extrai a API key do query parameter
    api_key = request.query_params.get("api_key")
    
    # Log para debug
    print(f"🔑 API key recebida: {api_key[:20]}..." if api_key else "❌ Nenhuma API key fornecida")
    
    # Valida se a API key foi fornecida
    if not api_key:
        return JSONResponse(
            status_code=401,
            content={
                "error": "API key é obrigatória",
                "detail": "Adicione ?api_key=sua-chave na URL",
                "example": f"{request.url.scheme}://{request.url.netloc}{request.url.path}?api_key=sua-chave"
            }
        )
    
    # Valida se a API key é válida
    if api_key != VALID_API_KEY:
        print(f"❌ API key inválida. Recebida: {api_key[:20]}..., Esperada: {VALID_API_KEY[:20]}...")
        return JSONResponse(
            status_code=401,
            content={
                "error": "API key inválida",
                "detail": "Verifique se você está usando a API key correta"
            }
        )
    
    # Se chegou até aqui, a API key é válida
    response = await call_next(request)
    return response


# ========================================
# EVENTO DE STARTUP
# ========================================
@app.on_event("startup")
async def startup_event():
    """Evento executado quando a aplicação inicia"""
    print("🚀 Iniciando aplicação...")
    try:
        # Pool já está inicializado no import (hardcoded)
        print("✅ Pool de conexões já inicializado (hardcoded)")

        # Marcar como inicializada
        mark_app_as_initialized()
        print("✅ Aplicação totalmente inicializada e pronta para receber requisições")
    except Exception as e:
        print(f"❌ ERRO CRÍTICO na inicialização: {e}")
        raise  # Força a aplicação a falhar na inicialização


# ========================================
# MIDDLEWARES (ordem importa!)
# ========================================
# 1. Middleware de segurança (ANTES DO CORS)
app.add_middleware(SecurityMiddleware)

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# EXCEPTION HANDLERS
# ========================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"return": exc.detail})


# ========================================
# ROUTERS
# ========================================
app.include_router(sistema.router)
app.include_router(estrutura.router)
app.include_router(alunos.router)


# ========================================
# MAIN (para execução direta)
# ========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

