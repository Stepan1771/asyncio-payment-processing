from fastapi import Depends

from api.depends import get_uow

from core.db import UnitOfWork

from services import PaymentService


def get_payment_service(
    uow: UnitOfWork = Depends(get_uow),
) -> PaymentService:
    return PaymentService(uow)