from loguru import logger
import httpx


async def get_odoo_backup(
        manager_link: str,
        db_name: str,
        password: str) -> bytes:
    backup_link = manager_link.replace("manager", "backup")
    try:
        async with httpx.AsyncClient() as cl:
            res = await cl.post(
                backup_link,
                data={
                    "master_pwd": password,
                    "name": db_name,
                    "backup_format": "zip"
                },
                timeout=None
            )
            res.raise_for_status()
    except httpx.HTTPError as err:
        logger.error(f"Error occurred while downloading backup - {str(err)}")
        raise OdooRequestError("Error while downloading backup.")
    return res.content


class OdooRequestError(Exception):
    pass
