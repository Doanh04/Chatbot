"""Shared metadata for chatbot models and externally owned table references."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def include_object(obj, name, type_, reflected, compare_to):
    """Alembic filter: migrate chatbot tables, never backend-owned tables."""
    if type_ == "table":
        if obj.info.get("external", False):
            return False
        # Do not propose dropping unrelated tables owned by the backend.
        if reflected and compare_to is None:
            return False
    return True
