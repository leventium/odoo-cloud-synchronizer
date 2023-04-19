from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from database import Database
from dependencies import get_database, get_request_data_from_cache
from responses import (
    SUCCESS_INSERTION,
    SUCCESS_DELETION,
    ODOO_INSTANCE_NOT_EXIST,
    serialize_instances
)


router = APIRouter(prefix="/authorized")


@router.get("/post_instance")
async def auth_post_instance(
        request_data: dict = Depends(get_request_data_from_cache),
        db: Database = Depends(get_database)):
    if not await db.user_exists(request_data["access_token"]):
        due_time = timedelta(seconds=int(request_data["expires_in"]))
        due_date = datetime.now() + due_time
        await db.insert_user(
            request_data["access_token"],
            request_data["refresh_token"],
            due_date.date()
        )
    await db.delete_odoo_instance(
        request_data["access_token"],
        request_data["url"],
        request_data["db_name"]
    )
    await db.insert_odoo_instance(
        request_data["access_token"],
        request_data["url"],
        request_data["db_name"],
        request_data["db_password"],
        int(request_data["cooldown"])
    )
    return SUCCESS_INSERTION


@router.get("/delete_instance")
async def auth_delete_instance(
        request_data: dict = Depends(get_request_data_from_cache),
        db: Database = Depends(get_database)):
    if await db.odoo_instance_exists(
            request_data["access_token"],
            request_data["url"],
            request_data["db_name"]):
        await db.delete_odoo_instance(
            request_data["access_token"],
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
    instances = await db.get_instances_of_user(request_data["access_token"])
    return serialize_instances(instances)
