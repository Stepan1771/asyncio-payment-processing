from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Payment,
    PaymentStatus,
)

from .base import BaseRepository


class PaymentRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Payment)

    async def create_payment(self, payment: Payment) -> Payment:
        self.session.add(payment)
        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def get_by_idempotency_key(
            self,
            key: str,
    ) -> Payment | None:
        result = await self.session.execute(
            select(Payment)
            .where(Payment.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        payment_uid: UUID,
        status: PaymentStatus,
        updated_at=None,
    ) -> Payment | None:
        payment = await self.get_by_uid(uid=payment_uid)
        if payment:
            payment.status = status
            if updated_at is not None:
                payment.updated_at = updated_at
            await self.session.flush()
        return payment