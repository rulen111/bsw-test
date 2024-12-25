import decimal
import enum
import time

import aioredis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_serializer


REDIS_EVENTS_URL = "redis://redis"


class BetStatus(enum.IntEnum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class Bet(BaseModel):
    bet_id: str
    event_id: str
    amount: decimal.Decimal
    status: BetStatus = BetStatus.NEW

    @field_serializer("amount")
    def serialize_amount(self, amount: decimal.Decimal, _info):
        return str(amount)


app = FastAPI()
r_client = aioredis.from_url(REDIS_EVENTS_URL)


@app.get("/events")
async def get_events():
    async with r_client.client() as conn:
        cur = b"0"
        while cur:
            cur, keys = await conn.scan(cur, match="event:*")
        result = list()
        for key in keys:
            values = await conn.hgetall(key)
            result.append(values)

    return result


@app.post("/bets")
async def make_bet(bet: Bet):
    async with r_client.client() as conn:
        key_event = f"event:{bet.event_id}"
        event = await conn.hgetall(key_event)
        if int(event[b"deadline"]) > int(time.time()):
            key_bet = f"bet:{bet.bet_id}"
            key_pair = f"event-bet:{bet.event_id}"
            data = bet.model_dump()
            async with conn.pipeline(transaction=True) as pipe:
                await (pipe.hset(key_bet, mapping=data).sadd(key_pair, bet.bet_id).execute())

    return {}


@app.get("/bets")
async def get_bets():
    async with r_client.client() as conn:
        cur = b"0"
        while cur:
            cur, keys = await conn.scan(cur, match="bet:*")
        result = list()
        for key in keys:
            value = await conn.hgetall(key)
            result.append(value)

    return result


@app.get("/bets/{bet_id}")
async def get_bet(bet_id: str):
    async with r_client.client() as conn:
        key = f"bet:{bet_id}"
        value = await conn.hgetall(key)
        if value:
            return value
        else:
            raise HTTPException(status_code=404, detail="Bet not found")
