from fastapi import (
    HTTPException,
    Security,
    status,
)
from fastapi.security import APIKeyHeader

from core.config import app_settings


_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    if not api_key or api_key != app_settings.auth.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-API-Key header",
        )
    return api_key