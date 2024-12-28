import asyncio
import logging
import os
from typing import Optional

import aiohttp
import aioredis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from common.models import EventState, Bet
from common.rqueue import RedisQueue
from redis_pool import pool


EVENTS_URL = os.getenv("EVENTS_URL", "http://line-provider:8080/events")


def get_redis() -> aioredis.Redis:
    return aioredis.Redis(connection_pool=pool, decode_responses=True)


async def start_consuming(rqueu: RedisQueue, input_queue: asyncio.Queue) -> None:
    while True:
        try:
            async with asyncio.timeout(1.):
                msg = await rqueu.consume()

            if msg is None:
                await asyncio.sleep(os.getenv("WORKER_CONSUME_TIMEOUT", 1.))
                continue

            await input_queue.put((msg, True))

            if msg == os.getenv("WORKER_CONSUME_STOPWORD", "STOP_CONSUME"):
                logging.warning(f"Consumer got stopword {msg}. Breaking the loop")
                break
        except asyncio.TimeoutError:
            continue


async def process_messages(input_queue: asyncio.Queue, output_queue: asyncio.Queue) -> None:
    while True:
        event_id, force = await input_queue.get()

        if event_id == os.getenv("WORKER_PROCESS_STOPWORD", "STOP_PROCESS"):
            await output_queue.put(None)
            logging.warning(f"Proccess message got stopword {event_id}. Breaking the loop")
            break

        event_id = int(event_id)
        event_state = await get_event_state(event_id)
        if event_state is None:
            logging.warning(f"Could not fetch event_state on event:{event_id}")
            continue

        await output_queue.put((event_id, event_state, force))


async def get_event_state(event_id: int) -> Optional[EventState]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(EVENTS_URL + f"/{event_id}") as resp:
                event = await resp.json()
                return event.get("state", None)
    except aiohttp.ClientError as e:
        logging.warning(f"Line provider could not return valid response to worker: {e}")
        return None


async def update_bet(output_queue: asyncio.Queue, db_session: AsyncSession) -> None:
    while True:
        data = await output_queue.get()

        if data is None:
            break

        event_id, event_state, force = data
        if force:
            stmt = (
                update(Bet)
                .where(Bet.event_id == event_id)
                .values(status=event_state)
            )
        else:
            stmt = (
                update(Bet)
                .where(Bet.event_id == event_id)
                .where(Bet.status == EventState.NEW)
                .values(status=event_state)
            )

        await db_session.execute(stmt)
        await db_session.commit()


async def sync_states(input_queue: asyncio.Queue, db_session: AsyncSession) -> None:
    while True:
        stmt = select(Bet.event_id).where(Bet.status == EventState.NEW)
        event_ids = (await db_session.execute(stmt)).scalars().all()

        for event_id in event_ids:
            await input_queue.put((event_id, False))

        await asyncio.sleep(os.getenv("SYNC_EVENT_STATES_TIMEOUT", 300))


async def main() -> None:
    rqueue = RedisQueue(get_redis(), os.getenv("REDIS_QUEUE_EVENTS_POSTFIX", "events"))
    db_session = get_session()
    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    tasks = []
    for _ in range(os.getenv("RQWORKER_NUM_WORKERS", 1)):
        tasks += [
            asyncio.create_task(start_consuming(rqueue, input_queue)),
            asyncio.create_task(process_messages(input_queue, output_queue)),
            asyncio.create_task(update_bet(output_queue, db_session)),
            asyncio.create_task(sync_states(input_queue, db_session))
        ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
