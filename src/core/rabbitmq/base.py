from faststream.rabbit import (
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
)


class BaseRabbitMQBroker:
    def __init__(self, url: str):
        self.broker = RabbitBroker(url)
        self._exchanges = []
        self._queues = []

    async def start(self):
        await self.broker.start()

    async def stop(self):
        await self.broker.stop()

    def declare_exchange(self, exchange: RabbitExchange):
        self._exchanges.append(exchange)

    def declare_queue(self, queue: RabbitQueue):
        self._queues.append(queue)

    async def setup_exchanges_queues(self):
        for exchange in self._exchanges:
            await self.broker.declare_exchange(exchange)

        for queue in self._queues:
            await self.broker.declare_queue(queue)