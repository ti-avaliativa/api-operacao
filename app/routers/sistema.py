"""
Router para endpoints de sistema (health, test, security)
"""
from fastapi import APIRouter
from datetime import datetime
from app.core.database import get_db_connection
from app.utils.text_utils import ai
from app.core.cache import cached

router = APIRouter(tags=["Sistema"])

# Variáveis globais para segurança (importadas do módulo principal)
BLOCKED_IPS = set()
attack_attempts = {}


@router.get("/")
def root():
    """Rota raiz da API"""
    return {"D": "It is not"}


@router.get("/{db}")
@cached(ttl_seconds=10)
async def validar_database(db: str):
    """Rota básica da API para validação de funcionamento"""
    db = ai(str(db))
    
    try:
        with get_db_connection() as connection:
            cursor = connection.cursor()
            # Executar USE {db} explicitamente
            cursor.execute(f"USE {db}")
            # Se chegou aqui, o banco existe
            cursor.close()
            return {"D": "It is working"}
    except Exception as e:
        print(f"Erro ao validar banco {db}: {str(e)}")
    
    return {"D": "It is NOT working"}


@router.get("/test")
async def test_endpoint():
    """Endpoint de teste para verificar se a API está funcionando"""
    return {
        "success": True,
        "message": "Endpoint de teste funcionando!",
        "timestamp": datetime.now().isoformat(),
        "routes_available": [
            "GET /import/info - Informações sobre importação de estrutura",
            "POST /import/completo - Importação de estrutura (CSV)",
            "POST /import/alunos/step1 - Upload e validação de alunos",
            "POST /import/alunos/step2 - Mapeamento de colunas",
            "POST /import/alunos/step3 - Detecção de conflitos",
            "POST /import/alunos/step4 - Resolução de conflitos",
            "POST /import/alunos/step5 - Importação final",
            "GET /import/alunos/status - Status da importação"
        ]
    }


# Endpoints de segurança
@router.get("/security/blocked-ips", tags=["Segurança"])
async def get_blocked_ips():
    """Lista IPs bloqueados"""
    return {"blocked_ips": list(BLOCKED_IPS)}


@router.post("/security/unblock-ip/{ip}", tags=["Segurança"])
async def unblock_ip(ip: str):
    """Desbloqueia um IP"""
    if ip in BLOCKED_IPS:
        BLOCKED_IPS.remove(ip)
        return {"message": f"IP {ip} desbloqueado"}
    return {"message": f"IP {ip} não estava bloqueado"}


@router.get("/security/stats", tags=["Segurança"])
async def security_stats():
    """Estatísticas de segurança"""
    return {
        "blocked_ips_count": len(BLOCKED_IPS),
        "attack_attempts": dict(attack_attempts),
        "total_attacks_detected": sum(attack_attempts.values())
    }

