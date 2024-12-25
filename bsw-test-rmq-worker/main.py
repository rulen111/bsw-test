import asyncio
import json
import time
from typing import Optional

import aio_pika
import aioredis

RMQ_URL = "amqp://rmuser:rmpassword@rabbitmq/"
MAIN_QUEUE = "events"
REDIS_EVENTS_URL = "redis://redis"
CONS_EVENT_STATES = (2, 3)


r_client = aioredis.from_url(REDIS_EVENTS_URL)


async def update_bet_status(
        r_client: aioredis.Redis,
        event_id: str,
        event_status: int
) -> None:
    key = f"event-bets:{event_id}"
    bet_ids = await r_client.smembers(key)
    if bet_ids:
        for bet_id in bet_ids:
            key = f"bet:{bet_id}"
            await r_client.hset(key, "bet_status", event_status)


async def update_event(
        r_client: aioredis.Redis,
        event_id: str,
        data: dict
) -> None:
    key = f"event:{event_id}"
    deadline: Optional[int] = data.get("deadline", None)

    ex_value = deadline - int(time.time()) if deadline else None
    if ex_value is None:
        await r_client.hset(key, mapping=data)
    elif ex_value > 0:
        async with r_client.pipeline(transaction=True) as pipe:
            await (pipe.hset(key, mapping=data).expire(key, ex_value).execute())


async def process_message(
        message: aio_pika.abc.AbstractIncomingMessage,
) -> None:
    async with message.process():
        data = json.loads(message.body)     # NOT DECIMAL
        event_id = data["event_id"]
        await update_event(r_client, event_id, data)

        event_status = data.get("state", None)
        if event_status in CONS_EVENT_STATES:
            await update_bet_status(r_client, event_id, event_status)


async def main() -> None:
    connection = await aio_pika.connect_robust(RMQ_URL)
    channel = await connection.channel()

    queue = await channel.declare_queue(MAIN_QUEUE, auto_delete=True)
    await queue.consume(process_message)

    try:
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
