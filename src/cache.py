"""
Module with caching class.
"""
import redis.asyncio as redis


class Cache:
    def __init__(self, connection_string: str):
        self.redis = redis.from_url(connection_string, decode_responses=True)

    async def close(self) -> None:
        await self.redis.close()

    async def put_record(self, uuid: str, **kwargs) -> None:
        await self.redis.hset(uuid, mapping=kwargs)
        await self.redis.expire(uuid, 1800)

    async def get_record(self, uuid) -> dict[str, str]:
        return await self.redis.hgetall(uuid)

    async def extend_record(self, uuid: str, **kwargs) -> None:
        storage = await self.redis.hgetall(uuid)
        storage.update(kwargs)
        await self.redis.hset(uuid, mapping=storage)

    async def delete_record(self, uuid: str) -> None:
        await self.redis.delete(uuid)

    async def record_exists(self, uuid: str) -> bool:
        return await self.redis.exists(uuid)
