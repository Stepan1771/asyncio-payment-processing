import asyncio

from faststream.rabbit import RabbitBroker

from core.logging import logger

from core.config import publisher_settings

from repositories import OutboxRepository


class OutboxPublisher:
    def __init__(
        self,
        session_factory,
        broker: RabbitBroker,
        queue: str,
        exchange: str,
    ):
        self.session_factory = session_factory
        self.broker = broker
        self.queue = queue
        self.exchange = exchange
        self._stopped = asyncio.Event()

    async def _publish_event(self, event) -> None:
        logger.info(f"Публикация ивента: outbox_event_id - {event.id}")
        await self.broker.publish(
            message=event.payload,
            queue=self.queue,
            exchange=self.exchange,
            headers={
                "outbox_event_id": str(event.id),
                "outbox_event_uid": str(event.uid),
                "created_at": event.created_at.isoformat(),
            },
        )

    async def _process_batch(self) -> int:
        async with self.session_factory() as session:
            outbox_repository = OutboxRepository(session)

            events = await outbox_repository.get_unprocessed(
                limit=publisher_settings.outbox_worker.batch_size,
            )

            if not events:
                return 0

            success_ids = []

            for event in events:
                try:
                    await self._publish_event(event)
                    success_ids.append(event.id)

                except Exception:
                    logger.exception(
                        f"Ошибка публикации ивента: outbox_event_id - {event.id}",
                    )

            if success_ids:
                await outbox_repository.mark_processed_bulk(ids=success_ids)

            await session.commit()

            logger.info(
                f"Всего ивентов: {len(events)}, "
                f"Опубликовано: {len(success_ids)}, "
                f"Ошибок: {len(events) - len(success_ids)}"
            )

            return len(success_ids)

    async def start(self) -> None:
        logger.info("Запуск outbox worker")

        while not self._stopped.is_set():
            try:
                processed = await self._process_batch()

                if processed == 0:
                    await asyncio.sleep(publisher_settings.outbox_worker.poll_interval)
                else:
                    await asyncio.sleep(0)

            except Exception:
                logger.exception("Outbox loop ошибка")
                await asyncio.sleep(publisher_settings.outbox_worker.error_backoff)

    async def stop(self) -> None:
        logger.info("Остановка outbox worker")
        self._stopped.set()
