from typing import Optional

import aioredis


class RedisQueue:
    def __init__(self, r_client: aioredis.Redis, name: str, namespace: str = "queue"):
        self.redis = r_client
        self.key = f"{namespace}:{name}"

    async def publish(self, msg: str) -> None:
        await self.redis.rpush(self.key, msg)

    async def consume(self) -> Optional[str]:
        return await self.redis.lpop(self.key)
