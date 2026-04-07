from collections.abc import AsyncGenerator

from typing import Any

from core.db import (
    UnitOfWork,
    db_client,
)


async def get_uow() -> AsyncGenerator[UnitOfWork, Any]:
    async with UnitOfWork(db_client.session_factory) as uow:
        yield uow