import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
import aioredis

from common.models import PydEvent, EventState
from common.rqueue import RedisQueue
from redis_pool import pool


events: dict[int, PydEvent] = {
    1: PydEvent(event_id=1, coefficient=1.2, deadline=int(time.time()) + 600, state=EventState.NEW),
    2: PydEvent(event_id=2, coefficient=1.15, deadline=int(time.time()) + 60, state=EventState.NEW),
    3: PydEvent(event_id=3, coefficient=1.67, deadline=int(time.time()) + 90, state=EventState.NEW)
}


app = FastAPI()


def get_redis() -> aioredis.Redis:
    return aioredis.Redis(connection_pool=pool, decode_responses=True)


async def send_msg(event_id: str) -> None:
    rqueue = RedisQueue(get_redis(), os.getenv("REDIS_QUEUE_EVENTS_POSTFIX", "events"))
    await rqueue.publish(event_id)


@app.put('/events')
async def create_event(event: PydEvent, background_tasks: BackgroundTasks) -> PydEvent:
    if event.state in (EventState.FINISHED_WIN, EventState.FINISHED_LOSE):
        background_tasks.add_task(send_msg, str(event.event_id))

    if event.event_id not in events:
        events[event.event_id] = event
        return event

    for p_name, p_value in event.dict(exclude_unset=True).items():
        setattr(events[event.event_id], p_name, p_value)

    return events[event.event_id]


@app.get('/events/{event_id}')
async def get_event(event_id: int) -> list[PydEvent]:
    if event_id in events:
        return [events[event_id]]

    raise HTTPException(status_code=404, detail="Event not found")


@app.get('/events')
async def get_events(finished: Optional[int] = None) -> list[Optional[PydEvent]]:
    if finished:
        return list(e for e in events.values() if e.state in (EventState.FINISHED_WIN, EventState.FINISHED_LOSE))
    else:
        return list(e for e in events.values() if time.time() < e.deadline)
