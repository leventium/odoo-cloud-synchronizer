from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from loguru import logger
from database import Database, StringTooLong
from dependencies import get_database, get_request_data_from_cache
from responses import (
    SUCCESS_INSERTION,
    SUCCESS_DELETION,
    ODOO_INSTANCE_NOT_EXIST,
    STRING_TOO_LONG,
    serialize_instances
)


router = APIRouter(prefix="/authorized")


@router.get("/post_instance")
async def auth_post_instance(
        request_data: dict = Depends(get_request_data_from_cache),
        db: Database = Depends(get_database)):
    if not await db.user_exists(int(request_data["yandex_id"])):
        due_time = timedelta(seconds=int(request_data["expires_in"]))
        due_date = datetime.now() + due_time
        try:
            await db.insert_user(
                int(request_data["yandex_id"]),
                request_data["access_token"],
                request_data["refresh_token"],
                due_date.date()
            )
        except StringTooLong:
            logger.critical("Yandex token is too long.")
            return
    await db.delete_odoo_instance(
        int(request_data["yandex_id"]),
        request_data["url"],
        request_data["db_name"]
    )
    try:
        await db.insert_odoo_instance(
            int(request_data["yandex_id"]),
            request_data["url"],
            request_data["db_name"],
            request_data["db_password"],
            int(request_data["cooldown"])
        )
    except StringTooLong:
        return STRING_TOO_LONG
    return SUCCESS_INSERTION


@router.get("/delete_instance")
async def auth_delete_instance(
        request_data: dict = Depends(get_request_data_from_cache),
        db: Database = Depends(get_database)):
    if await db.odoo_instance_exists(
            int(request_data["yandex_id"]),
            request_data["url"],
            request_data["db_name"]):
        await db.delete_odoo_instance(
            int(request_data["yandex_id"]),
            request_data["url"],
            request_data["db_name"]
        )
        return SUCCESS_DELETION
    else:
        return ODOO_INSTANCE_NOT_EXIST


@router.get("/get_instance")
async def auth_get_instance(
        request_data: dict = Depends(get_request_data_from_cache),
        db: Database = Depends(get_database)):
    instances = await db.get_instances_of_user(int(request_data["yandex_id"]))
    return serialize_instances(instances)
