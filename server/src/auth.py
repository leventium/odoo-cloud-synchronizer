from fastapi import APIRouter, Depends
from cache import Cache
from dependencies import get_cache
from yandex import (
    YandexID,
    YandexTimeoutError,
    YandexResponseError,
    WrongTokenError
)
from responses import (
    redirect_to,
    get_gateway_timeout_error,
    get_bad_gateway_error,
    get_bad_request_error
)


router = APIRouter()


@router.get("/accept_redirect")
async def redirect_from_yandex(
        code: str,
        state: str = None,
        cache: Cache = Depends(get_cache)):
    try:
        access_token, refresh_token, expires_in = \
            await YandexID.change_code_to_token(code)
        user_yandex_id = await YandexID.get_user_id(access_token)
    except YandexTimeoutError:
        return get_gateway_timeout_error(
            "Яндекс не ответил на наш запрос. Повторите попытку позже."
        )
    except YandexResponseError:
        return get_bad_gateway_error(
            "Произошла ошибка при обработке ответа Яндекса. Повторите запрос."
        )
    except WrongTokenError:
        return get_bad_request_error("Неверный токен.")
    await cache.extend_record(
        state,
        yandex_id=user_yandex_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in
    )
    redirect_url = (await cache.get_record(state))["redirect_url"]
    redirect_url = f"{redirect_url}?uuid={state}"
    return redirect_to(redirect_url)
