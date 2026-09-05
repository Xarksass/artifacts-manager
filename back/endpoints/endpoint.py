from __future__ import annotations

#import json
from abc import ABC
from collections.abc import Awaitable, Callable
from datetime import datetime

#from hashlib import sha256
from pathlib import Path
from typing import Any

from core.http import get_client
from core.logger import get_logger
from dotenv import load_dotenv
from fastapi_cache.decorator import cache
from httpx import HTTPStatusError
from models.cooldown import Cooldown

load_dotenv()

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

logger = get_logger(__name__,'endpoint')

cache_namespace = 'API'

#def _cache_path(key: str) -> Path:
#    return CACHE_DIR / f"{key}.json"

@cache(expire=600, namespace=cache_namespace)
async def fetch_data(path: str, params: dict[str,Any]|None = None) -> dict[str,Any]:
    #cache_key = sha256(
    #    f"{path.replace("/", "_")}:{json.dumps(params)}".encode()
    #).hexdigest()
    #cache_file = _cache_path(cache_key)
    
    #if cache_file.exists():
    #    logger.debug(f'[FILE_CACHE] {cache_file}')
    #    return json.loads(cache_file.read_text())

    if params is None: params = {}
    
    response = await get_client().get(path, params=params)
    response.raise_for_status()
    data = response.json()

    logger.debug('Response recieved from API')
    
    #cache_file.write_text(json.dumps(data))
    return data

_cached_fetchers: dict[str, Callable[..., Awaitable[dict[str, Any]]]] = {}

def _get_cached_fetch(namespace: str, expire: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    """Retourne la fonction de fetch cachée pour ce namespace, en la créant
    une seule fois (le décorateur @cache ne doit être appliqué qu'une fois
    par namespace, pas à chaque appel)."""
    if namespace not in _cached_fetchers:

        @cache(expire=expire, namespace=namespace)
        async def fetch_data(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
            if params is None:
                params = {}

            response = await get_client().get(path, params=params)
            response.raise_for_status()
            data = response.json()

            logger.debug(f'[{namespace}] Response received from API')
            return data

        _cached_fetchers[namespace] = fetch_data # type: ignore

    return _cached_fetchers[namespace]

class APIException(Exception):
    def __init__(self, message:str):
        self.message = message
        super().__init__(self.message)

class Endpoint(ABC):
    endpoint: str
    cooldown: Cooldown|None = None
    _cache_namespace: str
    _cache_expire: int = 600

    async def fetch(self, path:str|None = None) -> dict[str,Any]:
        url = f'{self.endpoint}/{path}' if path is not None else self.endpoint
    
        logger.debug(f'fetch -> {self.endpoint}'+(f'{path}' if path is not None else ''))
        try:
            fetch_data = _get_cached_fetch(self._cache_namespace, self._cache_expire)
            data = await fetch_data(url)
        except HTTPStatusError as e:
            logger.warning(e)
            return {}

        assert isinstance(data, dict)
        if "error" in data:
            if isinstance(data['error'], dict):
                logger.warning(f'{self.endpoint} - {data["error"]["message"]}')
            else:
                logger.warning(f'{self.endpoint} - {data["error"]!s}')
            return {}

        return data['data'];

    async def fetchAll(self, path:str|None = None, params: dict[str,Any]|None = None) -> list[dict[str,Any]]:
        if params is None: params = {}
        url = f'{self.endpoint}/{path}' if path is not None else self.endpoint

        logger.debug(f'fetchAll -> {self.endpoint}'+(f'/{path}' if path is not None else '')+f' | Params: {params!s}')
        try:
            fetch_data = _get_cached_fetch(self._cache_namespace, self._cache_expire)
            data = await fetch_data(url, params=params)
        except HTTPStatusError as e:
            logger.warning(e)
            return []

        assert isinstance(data, dict)
        if "error" in data:
            if isinstance(data['error'], dict):
                logger.warning(f'{self.endpoint} - {data["error"]["message"]}')
            else:
                logger.warning(f'{self.endpoint} - {data["error"]!s}')
            return []

        return data['data'];

    async def post(self, action: str, body: dict[str,Any]|list[dict[str,Any]]|None = None) -> dict[str,Any]:
        url = f'{self.endpoint}action/{action}'

        params: dict[str,Any] = {}
        if body is not None: params['json'] = body

        logger.debug(f"post -> {url} | Params: {params.get('json', {})}")
        response = await get_client().post(url, **params)
        data = response.json()
    
        if "error" in data:
            logger.warning(f'{self.endpoint} - {data["error"]["message"]}')
            return {}

        if "cooldown" in data['data']:
            cd = data['data']['cooldown']
            self.cooldown = Cooldown(
                cd['remaining_seconds'],
                datetime.fromisoformat(cd['expiration']),
            )
            
        return data;