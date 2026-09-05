import json
import os
from collections import deque
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from hashlib import md5
from typing import Any

import controllers
import httpx
import uvicorn
from core.cache_backend import LoggingRedisBackend
from core.http import close_client, init_client
from core.logger import get_logger
from core.task_pool import TaskPool
from dotenv import load_dotenv
from endpoints.characters import CharactersEndpoint
from fastapi import FastAPI, Request, Response, staticfiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from middlewares.ddos_middleware import DDOSMiddleware
from models.bank import Bank
from redis import asyncio as aioredis  # type: ignore
from utils.application_tools import load_routers

#import logging
#logging.getLogger("fastapi_cache").setLevel(logging.DEBUG)
#logging.getLogger("fastapi_cache").addHandler(logging.StreamHandler())
logger = get_logger(__name__,'main')

characters_endpoint = CharactersEndpoint()

logs: deque[str]|None = None

bank: Bank|None = None
load_dotenv()

def request_key_builder(
    func: Callable[...,Any],
    namespace: str = "",
    *,
    request: Request|None = None,
    response: Response|None = None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    """ Replacement of default_key_builder to ignore session and mailer args """
    filtered_kwargs = {}
    for k,v in kwargs.items():
        filtered_kwargs[k] = json.dumps(v) if isinstance(v, dict) else v
    cache_key = md5(
        f"{func.__module__}:{func.__name__}:{args}:{filtered_kwargs}".encode()
    ).hexdigest()
    return f"{namespace}:{cache_key}"

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # === Initialisation du cache
    redis = aioredis.from_url(f"redis://{os.getenv('CACHE_HOST','localhost')}", password=os.environ['REDIS_PASSWORD']) # type: ignore

    app.state.redis = redis

    FastAPICache.init(LoggingRedisBackend(redis), prefix="fastapi-cache", key_builder=request_key_builder)

    init_client(
        timeout=httpx.Timeout(10.0, connect=5.0),
        base_url=f"{os.environ['API_URL']}"
    )

    app.state.bank = await Bank()
    app.state.characters = await characters_endpoint.get_characters()
    app.state.pool = TaskPool()

    yield

    # ===== SHUTDOWN =====
    await close_client()

app = FastAPI(lifespan = lifespan)
app.mount('/public', staticfiles.StaticFiles(directory='static'))
app.add_middleware(DDOSMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv('VITE_URL',"http://localhost:5173")],  # l'origine de ton dev server Vite
    allow_methods=["*"],
    allow_headers=["*"],
)
load_routers(app, controllers)

if __name__ == "__main__":
    #curses.wrapper(lambda screen: asyncio.run(main(screen)))
    uvicorn.run(
        'server:app',
        host = os.getenv('UVICORN_HOST', '127.0.0.1'),
        port = 8000,
        reload = True
    )