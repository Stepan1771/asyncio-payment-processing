from faststream.rabbit import (
    RabbitMessage,
    RabbitQueue,
    RabbitExchange,
)

from core.logging.logger import logger


class PaymentDlgConsumer:
    def __init__(
            self,
            broker,
            queue: RabbitQueue,
            exchange: RabbitExchange,
    ):
        self.broker = broker
        self.queue = queue
        self.exchange = exchange

    async def handle(self, payload: dict, message: RabbitMessage):
        payment_uid = payload.get("payment_uid", "unknown")

        logger.critical(
            "DLQ: payment %s permanently failed. Payload: %s",
            payment_uid,
            payload,
        )

        await message.ack()

    def register(self):
        @self.broker.subscriber(
            queue=self.queue,
            exchange=self.exchange,
        )
        async def handler(payload: dict, message: RabbitMessage):
            await self.handle(payload, message)