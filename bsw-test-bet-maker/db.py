import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession, async_sessionmaker

import common.models as models

engine = create_async_engine(os.getenv("DB_URL"))


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
