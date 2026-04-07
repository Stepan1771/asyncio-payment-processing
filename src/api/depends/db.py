from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from core.db import db_client


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in db_client.get_session():
        yield session
