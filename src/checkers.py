import os
import asyncio
from urllib.parse import urlparse
from datetime import datetime, timedelta
from database import Database
from yandex import YandexID, YandexDisk, YandexResponseError
from odoo import get_odoo_backup, OdooRequestError
from loguru import logger


async def backup_odoo_instance(
        ya_token: str,
        odoo_url: str,
        db_name: str,
        db_password: str):
    disk = YandexDisk(ya_token)
    try:
        file = await get_odoo_backup(odoo_url, db_name, db_password)
        today = datetime.now().date()
        url = urlparse(odoo_url)
        await disk.put_file(f"{url.netloc}-{db_name}-"
                            f"{today.year}-{today.month}-"
                            f"{today.day}.zip", file)
        logger.info(f"{url.netloc}/{db_name} was successfully backup")
    except OdooRequestError:
        logger.error(
            "Odoo error was caught while making "
            f"backup - {odoo_url} - {db_name}"
        )
    except YandexResponseError:
        logger.error(
            "Yandex error was caught while "
            f"making backup - {odoo_url} - {db_name}"
        )
    finally:
        await disk.close()


async def refresh_yandex_tokens():
    db = await Database.connect(
        host=os.environ["PG_HOST"],
        port=int(os.environ["PG_PORT"]),
        username=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        database=os.environ["PG_DATABASE"]
    )
    try:
        users_to_refresh = await db.get_tokens_to_refresh()
        for user in users_to_refresh:
            try:
                token, refresh_token, expires_in = \
                    YandexID.get_new_token(user["refresh_token"])
            except YandexResponseError:
                logger.error("Yandex error was caught while refreshing token.")
                continue
            due_time = timedelta(seconds=expires_in)
            due_date = datetime.now() + due_time
            await db.update_user_token(
                yandex_id=user["id"],
                new_token=token,
                new_refresh_token=refresh_token,
                new_due_date=due_date.date()
            )
            logger.info(f"Refreshed token for {user['id']}")
    finally:
        await db.close()


async def backup_all_instances():
    db = await Database.connect(
        host=os.environ["PG_HOST"],
        port=int(os.environ["PG_PORT"]),
        username=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        database=os.environ["PG_DATABASE"]
    )
    try:
        instances = await db.get_odoo_instances_to_backup()
        await asyncio.gather(*[
            backup_odoo_instance(
                inst["token"],
                inst["url"],
                inst["db_name"],
                inst["db_password"]
            ) for inst in instances
        ])
    finally:
        await db.close()
