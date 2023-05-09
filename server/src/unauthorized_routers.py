import os
from uuid import uuid4
from fastapi import APIRouter, Depends
from dependencies import get_cache
from responses import redirect_to_yandex_oauth, WRONG_ODOO_URL_FORMAT
from cache import Cache


router = APIRouter()


@router.get("/post_instance")
async def post_instance(
        url: str,
        db_name: str,
        db_password: str,
        cooldown: int,
        cache: Cache = Depends(get_cache)):
    if not url.endswith("manager"):
        return WRONG_ODOO_URL_FORMAT
    request_id = str(uuid4())
    await cache.put_record(
        request_id,
        redirect_url=f"{os.environ['ROOT_PATH']}/authorized/post_instance",
        url=url,
        db_name=db_name,
        db_password=db_password,
        cooldown=cooldown
    )
    return redirect_to_yandex_oauth(request_id)


@router.get("/get_instance")
async def get_instance(cache: Cache = Depends(get_cache)):
    request_id = str(uuid4())
    await cache.put_record(
        request_id,
        redirect_url=f"{os.environ['ROOT_PATH']}/authorized/get_instance"
    )
    return redirect_to_yandex_oauth(request_id)


@router.get("/delete_instance")
async def get_instance(
        url: str,
        db_name: str,
        cache: Cache = Depends(get_cache)):
    request_id = str(uuid4())
    await cache.put_record(
        request_id,
        redirect_url=f"{os.environ['ROOT_PATH']}/authorized/delete_instance",
        url=url,
        db_name=db_name
    )
    return redirect_to_yandex_oauth(request_id)
