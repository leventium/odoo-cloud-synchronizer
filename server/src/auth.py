from fastapi import APIRouter, Depends
from cache import Cache
from dependencies import get_cache
from yandex import change_code_to_token
from responses import redirect_to


router = APIRouter()


@router.get("/accept_redirect")
async def redirect_from_yandex(
        code: str,
        state: str = None,
        cache: Cache = Depends(get_cache)):
    response = await change_code_to_token(code)
    await cache.extend_record(
        state,
        access_token=response["access_token"],
        expires_in=response["expires_in"],
        refresh_token=response["refresh_token"]
    )
    redirect_url = (await cache.get_record(state))["redirect_url"]
    redirect_url = f"{redirect_url}?uuid={state}"
    return redirect_to(redirect_url)
