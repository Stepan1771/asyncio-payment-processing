from fastapi import APIRouter

from api.v1.payments import router as payments_router

from core.config import app_settings


router = APIRouter(
    prefix=app_settings.api.v1.prefix,
)


router.include_router(payments_router)
