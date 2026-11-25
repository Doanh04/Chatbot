"""Import models here so Alembic can discover all chatbot tables."""

from chatbot.core.db.base import Base, include_object
from chatbot.core.db.models.chatbot import (
    CHATBOT_TABLES,
    ChatMessage,
    ChatSession,
    KnowledgeFile,
    KnowledgeFolder,
    session_files,
    session_folders,
)

__all__ = [
    "Base", "include_object", "CHATBOT_TABLES", "ChatMessage", "ChatSession",
    "KnowledgeFile", "KnowledgeFolder", "session_files", "session_folders",
]
