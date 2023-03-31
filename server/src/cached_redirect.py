from uuid import uuid4
from cache import Cache
from responses import redirect_to_yandex_oauth


async def redirect_insert_instance(
        cache_client: Cache,
        url: str,
        name: str,
        password: str,
        cooldown: int):
    """
    Redirect to yandex oauth and put in cache info, that user
    want to insert odoo instance and its credentials.
    :param cache_client: instance of Cache class
    :param url: url of odoo instance
    :param name: name of odoo database to back up
    :param password: password of odoo database
    :param cooldown: how often (days) we need to do back up
    :return: Redirect to yandex with STATE of uuid of record in cache
    """
    user_id = str(uuid4())
    await cache_client.put_record(
        user_id,
        action="insert",
        url=url,
        db_name=name,
        db_password=password,
        cooldown=cooldown
    )
    return redirect_to_yandex_oauth(user_id)


async def redirect_delete_instance(cache_client: Cache, url: str, name: str):
    """
    Redirect to yandex oauth and put in cache info, that user
    want to delete odoo instance and its credentials.
    :param cache_client: instance of Cache class
    :param url: url of odoo instance
    :param name: name of odoo database to back up
    :return:
    """
    user_id = str(uuid4())
    await cache_client.put_record(
        user_id,
        action="delete",
        url=url,
        db_name=name
    )
    return redirect_to_yandex_oauth(user_id)


async def redirect_get_instance(cache_client: Cache):
    """
    Redirect to yandex oauth and put in cache info, that user
    want to get info about his odoo instances.
    :param cache_client:
    :return:
    """
    user_id = str(uuid4())
    await cache_client.put_record(
        user_id,
        action="get"
    )
    return redirect_to_yandex_oauth(user_id)
