from psycopg_pool import AsyncConnectionPool
from app.config import DATABASE_URL

pool = AsyncConnectionPool(
    DATABASE_URL,
    min_size=1,
    max_size=5,
    timeout=10,
    kwargs={"prepare_threshold": 0},
    open=False,
)