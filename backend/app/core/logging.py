"""Structured logging configuration for the backend.

Provides a single `configure_logging` entry point (called once at startup
from `main.py`) and a `get_logger` helper so every module logs through a
consistently configured, JSON-friendly logger instead of ad hoc `print`
calls.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

LOG_FORMAT: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


class ContextLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that merges structured context into every log call."""

    def process(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Merge adapter-level context into the outgoing log record.

        Args:
            msg: The log message.
            kwargs: Keyword arguments passed to the logging call.

        Returns:
            A tuple of the (possibly augmented) message and kwargs.
        """

        extra = kwargs.get("extra", {})
        merged_extra = {**self.extra, **extra}
        kwargs["extra"] = merged_extra
        return msg, kwargs


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging handlers and format.

    Should be called exactly once, at application startup.

    Args:
        level: Logging level name (e.g. "DEBUG", "INFO", "WARNING").
    """

    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    if root_logger.handlers:
        # Avoid duplicate handlers if configure_logging is called more than once
        # (e.g. under a test runner that imports main multiple times).
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(handler)


def get_logger(name: str, **context: Any) -> logging.LoggerAdapter:
    """Get a named logger, optionally bound to structured context.

    Args:
        name: Logger name, typically `__name__` of the calling module.
        **context: Structured key/value context merged into every record,
            e.g. `get_logger(__name__, component="auth")`.

    Returns:
        A `LoggerAdapter` that behaves like a standard logger.
    """

    base_logger = logging.getLogger(name)
    return ContextLoggerAdapter(base_logger, context)
