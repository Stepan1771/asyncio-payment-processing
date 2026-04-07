from repositories import (
    PaymentRepository,
    OutboxRepository,
)


class UnitOfWork:
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory
        self.session = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = await self._session_factory().__aenter__()

        self.payment_repository = PaymentRepository(session=self.session)
        self.outbox_repository = OutboxRepository(session=self.session)

        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc:
            await self.session.rollback()
        else:
            pass

        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()