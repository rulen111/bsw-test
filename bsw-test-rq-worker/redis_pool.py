import os

import aioredis


def create_redis() -> aioredis.ConnectionPool:
    return aioredis.ConnectionPool.from_url(
        url=os.getenv("REDIS_QUEUE_URL", "redis://redis"),
        max_connections=os.getenv("REDIS_QUEUE_MAX_CONN", None),
    )


pool = create_redis()
