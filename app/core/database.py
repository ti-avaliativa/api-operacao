"""
Gerenciamento de conexões com banco de dados
Usa 1 pool global SEM banco específico + comando USE {db} em cada query
"""
import mysql.connector
import mysql.connector.pooling
from contextlib import contextmanager
from fastapi import HTTPException, Request
from app.core.config import DB_CONFIG, POOL_CONFIG

# Pool de conexões global (SEM banco específico)
pool = None

def initialize_pool():
    """
    Inicializa o pool de conexões SEM banco específico

    O banco será selecionado via comando USE {db} em cada query
    
    Raises:
        Exception: Se não conseguir conectar ao banco (aplicação não deve iniciar)
    """
    global pool

    try:
        # Criar pool SEM especificar database
        pool_config = {**POOL_CONFIG, **DB_CONFIG}
        # Remover 'database' se existir
        pool_config.pop('database', None)

        pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)

        print("✅ Pool de conexões MySQL inicializado (sem banco específico)")
        print("📊 Banco será selecionado via USE {db} em cada query")
        return True
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: Não foi possível conectar ao MySQL: {e}")
        print(f"❌ Verifique as variáveis de ambiente: DB_HOST, DB_USER, DB_PASSWORD")
        pool = None
        raise Exception(f"Failed to initialize database pool: {e}")




@contextmanager
def get_db_connection(db_name: str = None):
    """
    Context manager para obter conexão do pool

    IMPORTANTE: Se db_name for fornecido, executa USE {db_name} automaticamente

    Args:
        db_name: Nome do banco de dados (opcional)
    
    Raises:
        HTTPException: Se o pool não estiver inicializado ou houver erro de conexão
    """
    global pool

    if pool is None:
        raise HTTPException(
            status_code=503,
            detail="Database connection pool not initialized. Check database configuration."
        )

    connection = None
    cursor = None
    try:
        connection = pool.get_connection()

        # Se db_name foi fornecido, executar USE {db}
        if db_name:
            cursor = connection.cursor()
            cursor.execute(f"USE {db_name}")
            cursor.close()
            cursor = None
            print(f"🗄️ Usando banco: {db_name}")

        yield connection
    except mysql.connector.errors.PoolError as e:
        print(f"Pool error: {e}")
        raise HTTPException(status_code=503, detail="Database connection pool exhausted")
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_db_name_from_request(request: Request) -> str:
    """
    Extrai o nome do banco do request

    O nome do banco é definido pelo middleware database_selector_middleware
    e armazenado em request.state.db_name

    Args:
        request: FastAPI Request object

    Returns:
        Nome do banco de dados

    Raises:
        ValueError: Se db_name não estiver no request.state
    """
    if hasattr(request, "state") and hasattr(request.state, "db_name"):
        return request.state.db_name

    raise ValueError(
        "Nome do banco não encontrado no request. "
        "Certifique-se de que a URL está no formato: /api_operacao/{db_name}/endpoint"
    )


def test_connection():
    """Testa a conexão com o banco de dados"""
    global pool
    try:
        if pool is None:
            raise Exception("Database pool not initialized")
        
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        print("✅ Conexão com banco testada com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {e}")
        raise
        return False

