from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Header,
)
from starlette import status

from api.depends import (
    get_payment_service,
    verify_api_key,
)

from core.config import app_settings

from schemas.payment import CreatePaymentRequest

from services.payment import PaymentService


router = APIRouter(
    prefix=app_settings.api.v1.payments,
    tags=["Payments"],
)


@router.post(
    path="/",
    summary="Создание платежа",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_api_key)],
)
async def create_payment(
        service: Annotated[
            PaymentService,
            Depends(get_payment_service),
        ],
        body: CreatePaymentRequest,
        idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    return await service.create_payment(schema=body, idempotency_key=idempotency_key)


@router.get(
    path="/{payment_id}",
    summary="Получение информации о платеже",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key)],
)
async def get_payment(
        service: Annotated[
            PaymentService,
            Depends(get_payment_service),
        ],
        payment_id: int = Path(..., description="ID платежа"),
):
    return await service.get_payment_by_id(payment_id=payment_id)