from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine
from app.core.config import settings

_engine: Engine | None = None


def get_engine() -> Engine:
    """Retorna uma Engine única do SQLAlchemy conectada ao MySQL."""
    global _engine
    if _engine is None:
        url = (
            f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_APP_NAME}?charset=utf8mb4"
        )
        _engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=3600,
            future=True,
        )
    return _engine


def get_db() -> Generator[Connection, None, None]:
    """Dependency injection para rotas FastAPI obterem uma conexão ativa com o banco."""
    engine = get_engine()
    with engine.connect() as conn:
        yield conn
