"""Generic async repository providing common CRUD operations.

Repositories are the only layer that issues SQLAlchemy queries. They
contain zero business logic — validation, authorization, and orchestration
belong in the service layer that calls them.
"""

from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic CRUD repository parameterized over a single ORM model type."""

    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        """Initialize the repository.

        Args:
            session: The request-scoped async DB session to operate on.
            model: The SQLAlchemy model class this repository manages.
        """

        self._session = session
        self._model = model

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelType | None:
        """Fetch a single row by primary key.

        Args:
            entity_id: The UUID primary key to look up.

        Returns:
            The matching model instance, or None if not found.
        """

        return await self._session.get(self._model, entity_id)

    async def list_all(self, offset: int = 0, limit: int = 100) -> list[ModelType]:
        """List rows with basic pagination.

        Args:
            offset: Number of rows to skip.
            limit: Maximum number of rows to return.

        Returns:
            A list of model instances.
        """

        result = await self._session.execute(select(self._model).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def add(self, entity: ModelType) -> ModelType:
        """Add a new entity to the session and flush to obtain its id.

        Args:
            entity: The new, unsaved model instance.

        Returns:
            The same instance, refreshed with any database-generated defaults.
        """

        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        """Delete an entity from the session.

        Args:
            entity: The model instance to delete.
        """

        await self._session.delete(entity)
        await self._session.flush()
