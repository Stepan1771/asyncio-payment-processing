from datetime import datetime

from decimal import Decimal

from typing import (
    Any,
    Dict,
    Optional,
)

from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
)

from models.payment import (
    Currency,
    Payment,
    PaymentStatus,
)


class CreatePaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: Currency
    description: str = Field(min_length=1, max_length=500)
    metadata: Optional[Dict[str, Any]] = None
    webhook_url: str


class CreatePaymentDBSchema(BaseModel):
    amount: Decimal
    currency: Currency
    description: str
    meta: Optional[Dict[str, Any]] = None
    webhook_url: str
    idempotency_key: str
    status: PaymentStatus = PaymentStatus.PENDING


class CreatePaymentResponse(BaseModel):
    id: int
    status: PaymentStatus
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class PaymentResponse(BaseModel):
    id: int
    uid: UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] | None = None
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )

    @classmethod
    def from_orm_model(cls, payment: Payment) -> "PaymentResponse":
        return cls(
            id=payment.id,
            uid=payment.uid,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.meta,
            status=payment.status,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )