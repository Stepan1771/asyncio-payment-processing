from typing import (
    Any,
    TypeVar,
)

from uuid import UUID

from pydantic import BaseModel

from sqlalchemy import (
    delete,
    insert,
    select,
)

from sqlalchemy.ext.asyncio import AsyncSession


ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository:
    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelType],
    ):
        self.session = session
        self.model = model

    async def get_all(self) -> list[ModelType]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def get_by_id(self, obj_id: int) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return result.scalar()

    async def get_by_uid(self, uid: UUID) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).where(self.model.uid == uid)
        )
        return result.scalar()

    async def create(self, schema: CreateSchemaType) -> ModelType:
        result = await self.session.execute(
            insert(self.model)
            .values(schema.model_dump())
            .returning(self.model)
        )
        return result.scalar()

    async def create_bulk(self, schemas: list[BaseModel]) -> list[ModelType]:
        data = [s.model_dump() for s in schemas]
        objs = await self.session.execute(
            insert(self.model).values(data).returning(self.model)
        )
        return objs.scalars().all()

    async def remove(self, obj_id) -> None:
        await self.session.execute(
            delete(self.model).where(self.model.id == obj_id)
        )

    async def partial_update(
        self,
        uid: UUID,
        new_value: Any,
        value_name: str,
    ) -> None:
        obj = await self.get_by_uid(uid=uid)
        if obj:
            obj.__setattr__(value_name, new_value)
