import asyncio

from typing import (
    Any,
    Dict,
)

import httpx

from core.logging.logger import logger


class BaseHttpxClient:
    def __init__(
            self,
            max_concurrency: int,
            max_connections: int,
            max_keepalive: int,
            timeout_connect: float,
            timeout_read: float,
            timeout_write: float,
            timeout_pool: float,
    ):
        self._semaphore = asyncio.Semaphore(max_concurrency)
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive,
        )
        timeout = httpx.Timeout(
            connect=timeout_connect,
            read=timeout_read,
            write=timeout_write,
            pool=timeout_pool,
        )
        self._client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
        )

    async def close(self):
        await self._client.aclose()

    async def request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with self._semaphore:
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    json=json,
                    headers=headers,
                )
                response.raise_for_status()
                return response

            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                logger.error(
                    "HTTP %s %s failed: %s",
                    method,
                    url,
                    exc,
                )
                raise

    async def post(self, url: str, json: Dict[str, Any], **kwargs):
        return await self.request("POST", url, json=json, **kwargs)

    async def get(self, url: str, **kwargs):
        return await self.request("GET", url, **kwargs)