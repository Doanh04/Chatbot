"""Chat and knowledge models sharing PostgreSQL with the backend."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from chatbot.core.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Reference only: the backend owns the full users schema and its migrations.
# Never pass this table to create_all(); use include_object in Alembic env.py.
users = Table(
    "users",
    Base.metadata,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    info={"external": True},
)


session_folders = Table(
    "session_folders",
    Base.metadata,
    Column(
        "session_id", PgUUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), primary_key=True,
    ),
    Column(
        "folder_id", PgUUID(as_uuid=True),
        ForeignKey("knowledge_folders.id", ondelete="CASCADE"), primary_key=True,
    ),
)

session_files = Table(
    "session_files",
    Base.metadata,
    Column(
        "session_id", PgUUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), primary_key=True,
    ),
    Column(
        "file_id", PgUUID(as_uuid=True),
        ForeignKey("knowledge_files.id", ondelete="CASCADE"), primary_key=True,
    ),
)


class KnowledgeFolder(Base):
    """A knowledge folder owned by a backend user."""

    __tablename__ = "knowledge_folders"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow,
    )

    files: Mapped[list[KnowledgeFile]] = relationship(
        back_populates="folder", cascade="all, delete-orphan",
    )


class KnowledgeFile(Base):
    """A stored file, optionally organized into a knowledge folder."""

    __tablename__ = "knowledge_files"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("knowledge_folders.id"), nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(32), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow,
    )
    _metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    folder: Mapped[KnowledgeFolder | None] = relationship(back_populates="files")


class ChatSession(Base):
    """A conversation selecting knowledge folders and individual files."""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow,
    )

    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session", cascade="all, delete-orphan",
    )
    folders: Mapped[list[KnowledgeFolder]] = relationship(secondary=session_folders)
    files: Mapped[list[KnowledgeFile]] = relationship(secondary=session_files)


class ChatMessage(Base):
    """A user or assistant message, optionally carrying RAG sources."""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )

    session: Mapped[ChatSession] = relationship(back_populates="messages")


# Explicit ownership keeps the backend users table out of create_all().
CHATBOT_TABLES = tuple(
    table for table in Base.metadata.sorted_tables
    if not table.info.get("external", False)
)
