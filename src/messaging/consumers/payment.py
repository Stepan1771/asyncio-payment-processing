import asyncio

import random

from datetime import (
    datetime,
    timezone,
)

from uuid import UUID

from faststream.rabbit import (
    RabbitMessage,
    RabbitQueue,
    RabbitExchange,
)

from core.db import db_client

from core.httpx.base import BaseHttpxClient

from core.logging.logger import logger

from models import PaymentStatus

from repositories import PaymentRepository


class PaymentConsumer:
    def __init__(
            self,
            broker,
            httpx_client: BaseHttpxClient,
            max_retries: int,
            queue: RabbitQueue,
            exchange: RabbitExchange,
    ):
        self.broker = broker
        self.httpx_client = httpx_client
        self.max_retries = max_retries
        self.queue = queue
        self.exchange = exchange

    @staticmethod
    async def _payment_simulator() -> bool:
        logger.info("Эмуляция платежного шлюза")
        await asyncio.sleep(random.uniform(2, 5))
        return random.random() < 0.9

    @staticmethod
    async def _parse_message(payload: dict, message: RabbitMessage):
        retry_count = int(message.headers.get("x-retry-count", 0))
        payment_uid = payload.get("payment_uid")
        webhook_url = payload.get("webhook_url")

        if not payment_uid:
            logger.error("В сообщение отсутствует payment_uid - отбрасываем")
            await message.ack()
            return None

        return payment_uid, retry_count, webhook_url

    async def _update_status(self, payment_uid: str):
        payment_uid = UUID(payment_uid)

        success = await self._payment_simulator()
        new_status = PaymentStatus.SUCCEEDED if success else PaymentStatus.FAILED

        async with db_client.session_factory() as session:
            payment_repository = PaymentRepository(session)
            await payment_repository.update_status(
                payment_uid=payment_uid,
                status=new_status,
                updated_at=datetime.now(timezone.utc),
            )
            await session.commit()

        return new_status.value

    async def _send_webhook(self, webhook_url: str, payload: dict):
        if not webhook_url:
            logger.warning("Webhook URL не указан - пропускаем отправку")
            return

        await self.httpx_client.post(url=webhook_url, json=payload)

    async def _retry_or_dlq(self, payload, message, retry_count, payment_uid):
        if retry_count < self.max_retries - 1:
            delay = (2 ** (retry_count + 1)) + random.uniform(0, 0.5)

            logger.warning(
                "Retry %d/%d for payment %s in %.2fs",
                retry_count + 1,
                self.max_retries,
                payment_uid,
                delay,
            )

            await asyncio.sleep(delay)

            await self.broker.publish(
                payload,
                queue=self.queue,
                exchange=self.exchange,
                headers={"x-retry-count": retry_count + 1},
            )

            await message.ack()
        else:
            logger.critical(
                "Payment %s failed after %d attempts → DLQ",
                payment_uid,
                self.max_retries,
            )
            await message.nack(requeue=False)

    async def handler(self, payload: dict, message: RabbitMessage):
        parsed = await self._parse_message(payload, message)
        if not parsed:
            return

        payment_uid, retry_count, webhook_url = parsed

        try:
            status = await self._update_status(payment_uid)

            await self._send_webhook(
                webhook_url,
                {
                    "payment_uid": payment_uid,
                    "status": status,
                },
            )

            await message.ack()

        except Exception as exc:
            logger.error(
                "Payment processing failed %s: %s",
                payment_uid,
                exc,
            )

            await self._retry_or_dlq(
                payload,
                message,
                retry_count,
                payment_uid,
            )

    def register(self):
        @self.broker.subscriber(
            queue=self.queue,
            exchange=self.exchange,
        )
        async def main_handler(payload: dict, message: RabbitMessage):
            await self.handler(payload=payload, message=message)
