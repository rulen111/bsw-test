import decimal
import enum
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import aio_pika

RMQ_URL = "amqp://rmuser:rmpassword@rabbitmq/"
MAIN_QUEUE = "events"


class EventState(enum.IntEnum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class Event(BaseModel):
    event_id: str
    coefficient: Optional[decimal.Decimal] = None
    deadline: Optional[int] = None
    state: Optional[EventState] = None


events: dict[str, Event] = {
    '1': Event(event_id='1', coefficient=1.2, deadline=int(time.time()) + 600, state=EventState.NEW),
    '2': Event(event_id='2', coefficient=1.15, deadline=int(time.time()) + 60, state=EventState.NEW),
    '3': Event(event_id='3', coefficient=1.67, deadline=int(time.time()) + 90, state=EventState.NEW)
}


app = FastAPI()


async def events_publish(event: Event):
    connection = await aio_pika.connect_robust(RMQ_URL)
    data = event.model_dump_json(exclude_none=True)

    async with connection:
        routing_key = MAIN_QUEUE

        channel = await connection.channel()

        await channel.default_exchange.publish(
            aio_pika.Message(body=data.encode()),
            routing_key=routing_key,
        )


@app.put('/events')
async def create_event(event: Event, background_tasks: BackgroundTasks):
    if event.event_id not in events:
        events[event.event_id] = event
        background_tasks.add_task(events_publish, event)
        return {}

    background_tasks.add_task(events_publish, event)
    for p_name, p_value in event.dict(exclude_unset=True).items():
        setattr(events[event.event_id], p_name, p_value)

    return {}


@app.get('/events/{event_id}')
async def get_event(event_id: str):
    if event_id in events:
        return events[event_id]

    raise HTTPException(status_code=404, detail="Event not found")


@app.get('/events')
async def get_events():
    return list(e for e in events.values() if time.time() < e.deadline)
