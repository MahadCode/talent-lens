"""Alembic environment configuration.

Uses the same async SQLAlchemy engine configuration as the running app
(via `app.core.config.get_settings`) so migrations always target the same
database the API connects to, and runs synchronous migration operations
inside the async engine via `run_sync`, per SQLAlchemy 2.0's recommended
pattern for async-only projects.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import get_settings
from app.database.base import Base

# Import all models so `Base.metadata` is fully populated for autogenerate.
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

_settings = get_settings()
config.set_main_option("sqlalchemy.url", _settings.database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode, emitting SQL without a live DB connection."""

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: Connection) -> None:
    """Configure the migration context and run migrations on a sync connection.

    Args:
        connection: A synchronous connection proxy provided by `run_sync`.
    """

    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live async database connection."""

    connectable: AsyncEngine = create_async_engine(config.get_main_option("sqlalchemy.url"))

    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
