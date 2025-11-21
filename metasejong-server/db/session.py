from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from contextlib import contextmanager
from .config import settings


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.sqlalchemy_url,
            pool_size=settings.DB_POOL_SIZE,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={"connect_timeout": settings.DB_CONN_TIMEOUT},
        )
    return _engine


@contextmanager
def db_conn():
    engine = get_engine()
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()


# 헬스체크용 간단 쿼리
def quick_health():
    with db_conn() as conn:
        row = (
            conn.execute(
                text(
                    """
            SELECT 1 AS ok,
            (SELECT COUNT(*) FROM nodes) AS nodes_cnt,
            (SELECT COUNT(*) FROM edges) AS edges_cnt
            """
                )
            )
            .mappings()
            .first()
        )
    return dict(row)
