import os
from dotenv import load_dotenv
load_dotenv()
from loguru import logger
logger.add("logs.log", rotation="100 MB", level="INFO")
logger.add("errors.log", rotation="100 MB", level="ERROR")

from fastapi import FastAPI
import uvicorn
import auth
import authorized_routers
import unauthorized_routers
from database import Database


app = FastAPI()


@app.on_event("startup")
async def start():
    await Database.create_tables(
        os.environ["PG_HOST"],
        int(os.environ["PG_PORT"]),
        os.environ["PG_USER"],
        os.environ["PG_PASSWORD"],
        os.environ["PG_DATABASE"]
    )


app.include_router(auth.router)
app.include_router(authorized_routers.router)
app.include_router(unauthorized_routers.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
