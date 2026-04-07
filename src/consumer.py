import asyncio

from faststream import FastStream

from core.config import consumer_settings
from core.httpx.httpx_client import httpx_client
from core.logging import logger
from core.rabbitmq import RabbitMQBroker
from messaging.consumers.payment import PaymentConsumer
from messaging.consumers.payment_dlg import PaymentDlgConsumer

rmq = RabbitMQBroker()

payment_consumer = PaymentConsumer(
    broker=rmq.broker,
    httpx_client=httpx_client,
    max_retries=consumer_settings.consumer.max_retries,
    queue=rmq.payments_queue,
    exchange=rmq.payments_exchange,
)
payment_consumer.register()

dlq_consumer = PaymentDlgConsumer(
    broker=rmq.broker,
    queue=rmq.payments_dead_queue,
    exchange=rmq.payments_dlx_exchange,
)
dlq_consumer.register()

app = FastStream(rmq.broker)


@app.on_shutdown
async def on_shutdown() -> None:
    logger.info("Остановка consumer")
    await httpx_client.close()


if __name__ == "__main__":
    asyncio.run(app.run())


