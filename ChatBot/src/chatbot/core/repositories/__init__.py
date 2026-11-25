"""Database repositories for ChatBot entities."""

from chatbot.core.repositories.knowledge_folder import KnowledgeFolderRepository
from chatbot.core.repositories.knowledge_file import KnowledgeFileRepository

__all__ = ["KnowledgeFileRepository", "KnowledgeFolderRepository"]
