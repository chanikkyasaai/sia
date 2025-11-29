# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
import redis

from app.core.config import settings

# ---------- SQLAlchemy (Postgres) ----------

if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is required but not set in environment variables")

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=15,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency:
    from app.db.session import get_db
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Redis (snapshots / caching) ----------

redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,  # return str instead of bytes
)


def get_redis():
    """
    FastAPI dependency for Redis.
    """
    return redis_client


# Optional context manager if you need it outside FastAPI deps
@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
