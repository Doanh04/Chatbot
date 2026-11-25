"""CRUD operations for knowledge file records owned by a user."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chatbot.core.db.models import KnowledgeFile, KnowledgeFolder


class KnowledgeFileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: UUID,
        name: str,
        storage_key: str,
        storage_backend: str,
        folder_id: UUID | None = None,
        file_type: str | None = None,
        file_size: int | None = None,
        status: str = "pending",
        chunks: int = 0,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeFile:
        self._validate_values(
            {
                "name": name,
                "storage_key": storage_key,
                "storage_backend": storage_backend,
                "file_type": file_type,
                "file_size": file_size,
                "status": status,
                "chunks": chunks,
            }
        )
        await self._ensure_owned_folder(folder_id=folder_id, user_id=user_id)
        file = KnowledgeFile(
            user_id=user_id,
            folder_id=folder_id,
            name=name,
            storage_key=storage_key,
            storage_backend=storage_backend,
            file_type=file_type,
            file_size=file_size,
            status=status,
            chunks=chunks,
            error=error,
            _metadata=metadata,
        )
        self.session.add(file)
        await self.session.flush()
        return file

    async def get_by_id(self, *, file_id: UUID, user_id: UUID) -> KnowledgeFile | None:
        return await self.session.scalar(
            select(KnowledgeFile).where(
                KnowledgeFile.id == file_id,
                KnowledgeFile.user_id == user_id,
            )
        )

    async def list_by_user(
        self,
        *,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[KnowledgeFile]:
        self._validate_page(limit=limit, offset=offset)
        result = await self.session.scalars(
            select(KnowledgeFile)
            .where(KnowledgeFile.user_id == user_id)
            .order_by(KnowledgeFile.created_at.desc(), KnowledgeFile.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.all())

    async def list_by_folder_id(
        self,
        *,
        folder_id: UUID,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[KnowledgeFile]:
        self._validate_page(limit=limit, offset=offset)
        result = await self.session.scalars(
            select(KnowledgeFile)
            .where(
                KnowledgeFile.folder_id == folder_id,
                KnowledgeFile.user_id == user_id,
            )
            .order_by(KnowledgeFile.created_at.desc(), KnowledgeFile.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.all())

    async def update(
        self,
        *,
        file_id: UUID,
        user_id: UUID,
        changes: Mapping[str, Any],
    ) -> KnowledgeFile | None:
        allowed = {
            "folder_id", "name", "storage_key", "storage_backend", "file_type",
            "file_size", "status", "chunks", "error", "metadata",
        }
        invalid_fields = changes.keys() - allowed
        if invalid_fields:
            raise ValueError(f"Cannot update fields: {', '.join(sorted(invalid_fields))}")
        self._validate_values(changes)

        file = await self.get_by_id(file_id=file_id, user_id=user_id)
        if file is None:
            return None
        if "folder_id" in changes:
            await self._ensure_owned_folder(folder_id=changes["folder_id"], user_id=user_id)
        for field, value in changes.items():
            setattr(file, "_metadata" if field == "metadata" else field, value)
        await self.session.flush()
        return file

    async def delete(self, *, file_id: UUID, user_id: UUID) -> bool:
        file = await self.get_by_id(file_id=file_id, user_id=user_id)
        if file is None:
            return False
        await self.session.delete(file)
        await self.session.flush()
        return True

    async def _ensure_owned_folder(self, *, folder_id: UUID | None, user_id: UUID) -> None:
        if folder_id is None:
            return
        owned_folder_id = await self.session.scalar(
            select(KnowledgeFolder.id).where(
                KnowledgeFolder.id == folder_id,
                KnowledgeFolder.user_id == user_id,
            )
        )
        if owned_folder_id is None:
            raise ValueError("folder_id does not belong to user")

    @staticmethod
    def _validate_page(*, limit: int, offset: int) -> None:
        if limit < 1 or offset < 0:
            raise ValueError("limit must be positive and offset must be non-negative")

    @staticmethod
    def _validate_values(values: Mapping[str, Any]) -> None:
        text_limits = {"name": 255, "storage_key": 1024, "storage_backend": 32, "status": 32}
        for field, max_length in text_limits.items():
            if field in values:
                value = values[field]
                if not isinstance(value, str) or not value.strip() or len(value) > max_length:
                    raise ValueError(f"{field} must contain 1 to {max_length} characters")
        if "file_type" in values:
            value = values["file_type"]
            if value is not None and (not isinstance(value, str) or len(value) > 255):
                raise ValueError("file_type must contain at most 255 characters")
        for field in ("file_size", "chunks"):
            if field in values:
                value = values[field]
                if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                    raise ValueError(f"{field} must be a non-negative integer")
        if "chunks" in values and values["chunks"] is None:
            raise ValueError("chunks cannot be null")
