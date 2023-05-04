import os
from urllib.parse import urlparse, urlencode, urlunparse
from fastapi import Response, status
from fastapi.responses import RedirectResponse


YANDEX_OAUTH = "https://oauth.yandex.ru/authorize"


def redirect_to(url: str):
    return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)


def redirect_to_yandex_oauth(state: str = ""):
    redirect_url = list(urlparse(YANDEX_OAUTH))
    redirect_url[4] = urlencode({
        "response_type": "code",
        "client_id": os.environ["YANDEX_APP_ID"],
        "state": state
    })
    redirect_url = urlunparse(redirect_url)
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)


def serialize_instances(instances: list[dict]):
    if len(instances) == 0:
        result = "Empty."
    else:
        result = ""
        for inst in instances:
            result += f"{inst['url']}\t\t{inst['db_name']}\n"
    return Response(
        status_code=status.HTTP_200_OK,
        media_type="text/plain",
        content=result
    )


def get_gateway_timeout_error(text: str):
    return Response(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        media_type="text/plain",
        content=text
    )


def get_bad_gateway_error(text: str):
    return Response(
        status_code=status.HTTP_502_BAD_GATEWAY,
        media_type="text/plain",
        content=text
    )


def get_bad_request_error(text: str):
    return Response(
        status_code=status.HTTP_400_BAD_REQUEST,
        media_type="text/plain",
        content=text
    )


INVALID_TOKEN = Response(
    status_code=status.HTTP_401_UNAUTHORIZED,
    media_type="text/plain",
    content="Invalid token."
)

SUCCESS_INSERTION = Response(
    status_code=status.HTTP_201_CREATED,
    media_type="text/plain",
    content="Odoo instance inserted successfully."
)

SUCCESS_DELETION = Response(
    status_code=status.HTTP_201_CREATED,
    media_type="text/plain",
    content="Odoo instance deleted successfully."
)

ODOO_INSTANCE_NOT_EXIST = Response(
    status_code=status.HTTP_400_BAD_REQUEST,
    media_type="text/plain",
    content="Odoo instance with this URL and Database name doesn't exist."
)

STRING_TOO_LONG = Response(
    status_code=status.HTTP_400_BAD_REQUEST,
    media_type="text/plain",
    content="String is too long. URL max length is 140, "
            "DB_NAME - 80, DB_PASSWORD - 80."
)
