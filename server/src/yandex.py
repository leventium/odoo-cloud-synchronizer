"""
Module that provides wrapper under yandex API.
"""
import os
import httpx
from loguru import logger


class YandexDisk:
    def __init__(self, token: str):
        self.client = httpx.AsyncClient(
            base_url="https://cloud-api.yandex.net/v1/disk",
            headers={
                "Authorization": f"OAuth {token}"
            }
        )

    async def close(self):
        await self.close()

    async def check_token(self) -> bool:
        res = await self.client.get("/resources", params={"path": "app:/"})
        if 299 >= res.status_code >= 200:
            return True
        return False

    async def put_file(self) -> None:
        pass


class YandexID:
    @staticmethod
    async def change_code_to_token(code: str) -> tuple[str, str, int]:
        """
        Method requesting yandex to change authentication code to token.
        Can raise *YandexTimeoutError* and *YandexResponseError*.
        :param code: code that was got from yandex redirection.
        :return:
        access_token,
        refresh_token,
        expires_in
        """
        async with httpx.AsyncClient() as cl:
            try:
                res = await cl.post(
                    "https://oauth.yandex.ru/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code
                    },
                    auth=(
                        os.environ["YANDEX_APP_ID"],
                        os.environ["YANDEX_APP_SECRET"]
                    ))
            except httpx.TimeoutException:
                logger.error("Time limit exceeded while changing code to token.")
                raise YandexTimeoutError("Yandex didn't respond.")
        if res.status_code // 100 == 2:
            json_res = res.json()
            return (
                json_res["access_token"],
                json_res["refresh_token"],
                json_res["expires_in"]
            )
        logger.error("Yandex responded something other than 200.")
        logger.error(f"Response code: {res.status_code}.")
        logger.error(f"Response text: {res.text}")
        raise YandexResponseError(
            "Something went wrong, yandex responded not with HTTP 200."
        )

    @staticmethod
    async def get_user_id(token: str) -> int:
        """
        Method requesting yandex API to get user id
        in yandex system from access token.
        Can raise *YandexTimeoutError*, *WrongTokenError*
        and *YandexResponseError*.
        :param token: access token of user.
        :return: user's id in yandex's system
        """
        async with httpx.AsyncClient() as cl:
            try:
                res = await cl.get(
                    "https://login.yandex.ru/info",
                    headers={"Authorization": f"OAuth {token}"}
                )
            except httpx.TimeoutException:
                logger.error(
                    "Time limit exceeded while getting user id from token."
                )
                raise YandexTimeoutError("Yandex didn't respond.")
        if res.status_code // 100 == 2:
            return res.json()["id"]
        if res.status_code == 401:
            logger.warning("Wrong token got while getting user id.")
            raise WrongTokenError("Wrong token.")
        logger.error("Yandex responded something other than 200.")
        logger.error(f"Response code: {res.status_code}.")
        logger.error(f"Response text: {res.text}")
        raise YandexResponseError(
            "Something went wrong, yandex responded not with HTTP 200."
        )


class YandexResponseError(Exception):
    pass


class WrongTokenError(Exception):
    pass


class YandexTimeoutError(Exception):
    pass
