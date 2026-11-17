import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

Base = declarative_base()

# Determine database engine
db_url = settings.DATABASE_URL
if settings.USE_SQLITE_FALLBACK and ("sqlite" in db_url or not os.getenv("USE_POSTGRES_ONLY")):
    # Try testing postgres or fallback
    pass

# We support dynamic connection with fallback
engine = None
AsyncSessionLocal = None

def get_engine():
    global engine, AsyncSessionLocal
    if engine is None:
        target_url = settings.DATABASE_URL
        # In non-docker local Windows environments where Postgres isn't up, fallback to SQLite
        if settings.USE_SQLITE_FALLBACK:
            # Check if we should use SQLite
            target_url = settings.SQLITE_DATABASE_URL
        
        connect_args = {}
        if "sqlite" in target_url:
            connect_args = {"check_same_thread": False}

        engine = create_async_engine(
            target_url,
            echo=False,
            future=True,
            connect_args=connect_args
        )
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return engine

def get_sessionmaker():
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        get_engine()
    return AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
