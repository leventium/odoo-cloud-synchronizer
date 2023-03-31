import os
from urllib.parse import urlencode
import httpx
from dotenv import load_dotenv
load_dotenv()


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


async def change_code_to_token(code: str) -> dict:
    async with httpx.AsyncClient() as cl:
        res = await cl.post(
            "https://oauth.yandex.ru/token",
            data=urlencode({
                "grant_type": "authorization_code",
                "code": code
            }),
            auth=(
                os.environ["YANDEX_CLIENT_TOKEN"],
                os.environ["YANDEX_CLIENT_SECRET"]
            ))
    return res.json()
