"""Async SQLAlchemy engine and session management.

Exposes a single `get_db_session` FastAPI dependency so routes and
services never construct sessions themselves — all session lifecycle
(commit on success, rollback on error, always close) is handled here.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

_settings = get_settings()
_is_sqlite = _settings.database_url.startswith("sqlite")

_engine_kwargs: dict = {
    "echo": not _settings.is_production,
    "pool_pre_ping": not _is_sqlite,
}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    if ":memory:" in _settings.database_url:
        _engine_kwargs["poolclass"] = StaticPool

engine: AsyncEngine = create_async_engine(_settings.database_url, **_engine_kwargs)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped async DB session.

    Commits the transaction if the request handler completes without
    raising, rolls back on any exception, and always closes the session.

    Yields:
        An `AsyncSession` bound to the shared engine.
    """

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
