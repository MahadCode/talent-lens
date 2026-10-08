"""Column types that work on both PostgreSQL and SQLite."""

from sqlalchemy import JSON, Uuid

GUID = Uuid(as_uuid=True)
JSONType = JSON
