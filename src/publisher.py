import asyncio

from core.config import broker_settings

from core.db.db_client import db_client

from core.logging import logger

from core.rabbitmq import RabbitMQBroker

from messaging.publishers.outbox import OutboxPublisher


async def main() -> None:
    logger.info("Запуск publisher")

    rmq = RabbitMQBroker()
    await rmq.start()
    await rmq.setup()

    publisher = OutboxPublisher(
        session_factory=db_client.session_factory,
        broker=rmq.broker,
        queue=broker_settings.broker.payments_queue_routing_key,
        exchange=broker_settings.broker.payments_exchange,
    )

    try:
        await publisher.start()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await publisher.stop()
        await rmq.stop()
        await db_client.dispose()
        logger.info("Publisher остановлен")


if __name__ == "__main__":
    asyncio.run(main())

