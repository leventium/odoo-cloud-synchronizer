import time
import asyncio
from checkers import refresh_yandex_tokens, backup_all_instances
from loguru import logger


async def sync():
    while True:
        logger.info("Going to refresh tokens and backup odoo instances.")
        await refresh_yandex_tokens()
        await backup_all_instances()
        time.sleep(3600 * 10)


def main():
    time.sleep(10)
    asyncio.run(sync())
