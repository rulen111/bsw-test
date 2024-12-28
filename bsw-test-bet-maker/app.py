import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional, Sequence, Type

import aiohttp
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import init_db, get_session
from common.models import PydEvent, PydBet, Bet

EVENTS_URL = os.getenv("EVENTS_URL", "http://line-provider:8080/events")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/events")
async def get_events() -> list[Optional[PydEvent]]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(EVENTS_URL) as resp:
                return await resp.json()
    except aiohttp.ClientError as e:
        logging.warning(f"Line provider could not return valid response: {e}")
        raise HTTPException(status_code=424, detail="Line provider not responding correctly")


@app.post("/bets")
async def make_bet(
    bet: PydBet,
    db_session: AsyncSession = Depends(get_session),
) -> PydBet:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(EVENTS_URL + f"/{bet.event_id}") as resp:
                event = await resp.json()

        deadline = event[0].get("deadline", None)
        ex_value = deadline - int(time.time()) if deadline else None
        if not ex_value or ex_value < 0:
            raise HTTPException(status_code=400, detail="Betting deadline is already reached")

        bet_orm = Bet(**bet.model_dump())
        db_session.add(bet_orm)
        await db_session.commit()
        return bet

    except aiohttp.ClientError as e:
        logging.warning(f"Line provider could not return valid response: {e}")
        raise HTTPException(status_code=424, detail="Line provider not responding correctly")


@app.get("/bets")
async def get_bets(
    db_session: AsyncSession = Depends(get_session),
) -> Sequence[PydBet]:
    stmt = select(Bet)
    result = await db_session.execute(stmt)

    return result.scalars().all()


@app.get("/bets/{bet_id}")
async def get_bet(
    bet_id: int,
    db_session: AsyncSession = Depends(get_session),
) -> Type[PydBet]:
    bet = await db_session.get(PydBet, bet_id)
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")

    return bet
