from datetime import (
    datetime,
    timezone, UTC,
)

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import Outbox

from .base import BaseRepository


class OutboxRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Outbox)

    async def create_event(self, event: Outbox) -> Outbox:
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_unprocessed(
            self,
            limit: int = 100,
    ) -> list[Outbox]:
        result = await self.session.execute(
            select(Outbox)
            .where(Outbox.processed.is_(False))
            .order_by(Outbox.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def mark_processed_bulk(self, ids: list):
        await self.session.execute(
            update(Outbox)
            .where(Outbox.id.in_(ids))
            .values(processed=True, updated_at=datetime.now(UTC))
        )