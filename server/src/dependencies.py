import os
from fastapi import HTTPException, status
from database import Database
from cache import Cache


async def get_database():
    db = await Database.connect(
        host=os.environ["PG_HOST"],
        port=int(os.environ["PG_PORT"]),
        username=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        database=os.environ["PG_DATABASE"]
    )
    try:
        yield db
    finally:
        await db.close()


async def get_cache():
    cache = Cache(os.environ["REDIS_CONNSTRING"])
    try:
        yield cache
    finally:
        await cache.close()


async def get_request_data_from_cache(uuid: str):
    cache = Cache(os.environ["REDIS_CONNSTRING"])
    try:
        if await cache.record_exists(uuid):
            yield cache.get_record(uuid)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Данные запроса не найдены."
            )
    finally:
        await cache.delete_record(uuid)
        await cache.close()
