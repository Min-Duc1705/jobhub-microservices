import asyncio
import json
import logging

import aio_pika

from app.config import settings

logger = logging.getLogger(__name__)

_connection: aio_pika.abc.AbstractRobustConnection | None = None


async def get_rabbitmq_connection():
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    return _connection


async def publish(exchange_name: str, routing_key: str, payload: dict):
    """Publish a message đến RabbitMQ (dùng khi cần fanout kết quả)."""
    conn = await get_rabbitmq_connection()
    async with conn.channel() as channel:
        exchange = await channel.declare_exchange(
            exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )
