"""CRUD operations for folders owned by a user."""

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chatbot.core.db.models import KnowledgeFolder


class KnowledgeFolderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: UUID,
        name: str,
        description: str | None = None,
    ) -> KnowledgeFolder:
        self._validate_name(name)
        folder = KnowledgeFolder(
            user_id=user_id,
            name=name,
            description=description,
        )
        self.session.add(folder)
        await self.session.flush()
        return folder

    async def get_by_id(self, *, folder_id: UUID, user_id: UUID) -> KnowledgeFolder | None:
        result = await self.session.execute(
            select(KnowledgeFolder).where(
                KnowledgeFolder.id == folder_id,
                KnowledgeFolder.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        *,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[KnowledgeFolder]:
        if limit < 1 or offset < 0:
            raise ValueError("limit must be positive and offset must be non-negative")
        result = await self.session.scalars(
            select(KnowledgeFolder)
            .where(KnowledgeFolder.user_id == user_id)
            .order_by(KnowledgeFolder.created_at.desc(), KnowledgeFolder.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.all())

    async def update(
        self,
        *,
        folder_id: UUID,
        user_id: UUID,
        changes: Mapping[str, str | None],
    ) -> KnowledgeFolder | None:
        invalid_fields = changes.keys() - {"name", "description"}
        if invalid_fields:
            raise ValueError(f"Cannot update fields: {', '.join(sorted(invalid_fields))}")
        if "name" in changes:
            self._validate_name(changes["name"])

        folder = await self.get_by_id(folder_id=folder_id, user_id=user_id)
        if folder is None:
            return None
        for field, value in changes.items():
            setattr(folder, field, value)
        await self.session.flush()
        return folder

    async def delete(self, *, folder_id: UUID, user_id: UUID) -> bool:
        folder = await self.get_by_id(folder_id=folder_id, user_id=user_id)
        if folder is None:
            return False
        await self.session.delete(folder)
        await self.session.flush()
        return True

    @staticmethod
    def _validate_name(name: str | None) -> None:
        if name is None or not name.strip() or len(name) > 255:
            raise ValueError("name must contain 1 to 255 characters")
