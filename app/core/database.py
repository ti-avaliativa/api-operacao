"""
Gerenciamento de conexões com banco de dados
Pool hardcoded - SEM variáveis de ambiente
"""
import mysql.connector
import mysql.connector.pooling
from contextlib import contextmanager
from fastapi import HTTPException

# Pool de conexões global inicializado diretamente (hardcoded)
pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="my_pool",
    pool_size=10,
    pool_reset_session=True,
    host="av-rede.ctrnya9tildy.us-west-2.rds.amazonaws.com",
    port=3306,
    user="avaliaredeApiOperacao",
    password="Ti@valiativa$%2025",
    autocommit=True,
    connection_timeout=30,
    buffered=True,
    compress=False,
    charset='utf8mb4',
    collation='utf8mb4_general_ci'
)

print("✅ Pool de conexões MySQL inicializado com sucesso")

@contextmanager
def get_db_connection():
    """
    Context manager para obter conexão do pool
    """
    connection = None
    try:
        connection = pool.get_connection()
        yield connection
    except mysql.connector.errors.PoolError as e:
        print(f"Pool error: {e}")
        raise HTTPException(status_code=503, detail="Database connection pool exhausted")
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if connection and connection.is_connected():
            connection.close()

