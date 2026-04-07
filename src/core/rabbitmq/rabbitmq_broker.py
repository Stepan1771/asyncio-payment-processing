from faststream.rabbit import (
    RabbitExchange,
    ExchangeType,
    RabbitQueue,
)

from .base import BaseRabbitMQBroker

from core.config import broker_settings


class RabbitMQBroker(BaseRabbitMQBroker):
    def __init__(self):
        super().__init__(url=broker_settings.broker.url)

        self.payments_dlx_exchange = RabbitExchange(
            name=broker_settings.broker.payments_dlx_exchange,
            type=ExchangeType.DIRECT,
            durable=True,
        )
        self.payments_dead_queue = RabbitQueue(
            name=broker_settings.broker.payments_dead_queue,
            durable=True,
            routing_key=broker_settings.broker.payments_dead_queue_routing_key,
        )

        self.payments_exchange = RabbitExchange(
            name=broker_settings.broker.payments_exchange,
            type=ExchangeType.DIRECT,
            durable=True,
        )
        self.payments_queue = RabbitQueue(
            name=broker_settings.broker.payments_queue,
            durable=True,
            routing_key=broker_settings.broker.payments_queue_routing_key,
            arguments={  # type: ignore[arg-type]
                "x-dead-letter-exchange": broker_settings.broker.payments_dlx_exchange,
                "x-dead-letter-routing-key": broker_settings.broker.payments_dead_queue_routing_key,
            },
        )

        self.declare_exchange(self.payments_dlx_exchange)
        self.declare_queue(self.payments_dead_queue)
        self.declare_exchange(self.payments_exchange)
        self.declare_queue(self.payments_queue)

    async def setup(self):
        await self.setup_exchanges_queues()
