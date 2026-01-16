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
        print(f"❌ Erro ao conectar com MySQL: {e}")
        print("⚠️  API funcionará em modo DEMO (sem banco de dados)")
        pool = None
        return False




@contextmanager
def get_db_connection(db_name: str = None):
    """
    Context manager para obter conexão do pool

    IMPORTANTE: Se db_name for fornecido, executa USE {db_name} automaticamente

    Args:
        db_name: Nome do banco de dados (opcional)
    """
    global pool

    if pool is None:
        # Modo DEMO: simula conexão
        class MockConnection:
            def __init__(self):
                self.autocommit = True

            def cursor(self, dictionary=False):
                class MockCursor:
                    def execute(self, query, params=None):
                        print(f"📋 DEMO - Query: {query[:50]}..." if len(query) > 50 else f"📋 DEMO - Query: {query}")
                        if params:
                            print(f"📋 DEMO - Params: {params}")
                    def fetchone(self):
                        return None
                    def fetchall(self):
                        return []
                    def close(self):
                        pass
                    @property
                    def lastrowid(self):
                        return 1
                return MockCursor()

            def is_connected(self):
                return True

            def close(self):
                pass

            def commit(self):
                print("📋 DEMO - COMMIT")
                pass

            def rollback(self):
                print("📋 DEMO - ROLLBACK")
                pass

        yield MockConnection()
        return

    # Modo NORMAL: usa pool real
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
        if connection and connection.is_connected():
            connection.rollback()  # Rollback em caso de erro
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            # Commit antes de fechar a conexão
            try:
                connection.commit()
                print("✅ Transação confirmada (COMMIT)")
            except Exception as e:
                print(f"⚠️ Erro ao fazer commit: {e}")
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
        if pool is not None:
            with get_db_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            print("✅ Conexão com banco testada com sucesso")
            return True
        else:
            print("⚠️  Executando em modo DEMO (sem banco)")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {e}")
        return False

