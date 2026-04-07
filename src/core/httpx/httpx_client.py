from .base import BaseHttpxClient

from core.config import httpx_settings


httpx_client = BaseHttpxClient(
    max_concurrency=httpx_settings.httpx.max_concurrency,
    max_connections=httpx_settings.httpx.max_connections,
    max_keepalive=httpx_settings.httpx.max_keepalive,
    timeout_connect=httpx_settings.httpx.timeout_connect,
    timeout_read=httpx_settings.httpx.timeout_read,
    timeout_write=httpx_settings.httpx.timeout_write,
    timeout_pool=httpx_settings.httpx.timeout_pool,
)