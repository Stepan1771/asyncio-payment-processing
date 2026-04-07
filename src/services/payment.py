from core.db import UnitOfWork

from core.logging import logger
from schemas.outbox import CreateOutboxEvent
from schemas.payment import (
    CreatePaymentRequest,
    CreatePaymentDBSchema,
    CreatePaymentResponse,
    PaymentResponse,
)


class PaymentService:
    def __init__(
            self,
            unit_of_work: UnitOfWork,
    ):
        self.uow = unit_of_work

    async def create_payment(
            self,
            schema: CreatePaymentRequest,
            idempotency_key: str,
    ):
        logger.info("Создание платежа и ивента")

        payment_exist = await self.uow.payment_repository.get_by_idempotency_key(
            key=idempotency_key,
        )
        if payment_exist:
            logger.info("Платеж с таким idempotency_key уже существует")
            return CreatePaymentResponse(
                id=payment_exist.id,
                status=payment_exist.status,
                created_at=payment_exist.created_at,
            )

        db_schema = CreatePaymentDBSchema(
            amount=schema.amount,
            currency=schema.currency,
            description=schema.description,
            meta=schema.metadata,
            webhook_url=schema.webhook_url,
            idempotency_key=idempotency_key,
        )

        payment = await self.uow.payment_repository.create(schema=db_schema)

        outbox_event_schema = CreateOutboxEvent(
            payload={
                "payment_id": payment.id,
                "payment_uid": str(payment.uid),
                "amount": str(payment.amount),
                "currency": payment.currency.value,
                "description": payment.description,
                "webhook_url": payment.webhook_url,
            },
        )

        await self.uow.outbox_repository.create(schema=outbox_event_schema)

        await self.uow.commit()

        return CreatePaymentResponse(
            id=payment.id,
            status=payment.status,
            created_at=payment.created_at,
        )

    async def get_payment_by_id(self, payment_id: int) -> PaymentResponse | None:
        payment = await self.uow.payment_repository.get_by_id(payment_id)
        if not payment:
            return None
        return PaymentResponse.from_orm_model(payment)

