from __future__ import annotations

import os
from abc import ABC
from datetime import datetime
from typing import Any, NamedTuple

import requests
from dotenv import load_dotenv

from core.logger import get_logger

load_dotenv()

logger = get_logger(__name__,'endpoint')

class APIException(Exception):
    def __init__(self, message:str):
        self.message = message
        super().__init__(self.message)

class Cooldown(NamedTuple):
    remaining: int
    expiration: datetime

class Headers(NamedTuple):
    Accept: str
    ContentType: str
    Authorization: str

    def json(self) -> dict[str,str]:
        return {
            "Accept": self.Accept,
            "Content-Type": self.ContentType,
            "Authorization": self.Authorization
        }

class Endpoint(ABC):
    url: str = os.environ['API_URL']
    endpoint: str
    cooldown: Cooldown|None = None
    headers: Headers = Headers("application/json", "application/json", f"Bearer {os.environ['TOKEN']}")

    def __init__(self) -> None:
        super().__init__()
        self.url = f'{self.url}{self.endpoint}'

    def fetch(self, path:str|None = None) -> dict[str,Any]:
        url = f'{self.url}/{path}' if path is not None else self.url

        logger.info(f'fetch -> {self.endpoint}'+(f'/{path}' if path is not None else ''))
        response = requests.get(url, headers=self.headers.json())
        data = response.json()

        if "error" in data:
            logger.warning(f'{self.endpoint} - {data["error"]["message"]}')
            return {}

        return data['data'];

    def fetchAll(self, path:str|None = None, params: dict[str,Any]|None = None) -> list[dict[str,Any]]:
        if params is None: params = {}
        url = f'{self.url}/{path}' if path is not None else self.url

        logger.info(f'fetchAll -> {self.endpoint}'+(f'/{path}' if path is not None else '')+' | Params: {params}')
        response = requests.get(url, headers=self.headers.json(), params=params)
        data = response.json()

        if "error" in data:
            logger.warning(f'{self.endpoint} - {data["error"]["message"]}')
            return []

        return data['data'];

    async def post(self, action: str, body: dict[str,Any]|list[dict[str,Any]]|None = None) -> dict[str,Any]:
        url = f'{self.url}action/{action}'

        params: dict[str,dict[str,Any]|list[dict[str,Any]]] = {"headers": self.headers.json()}
        if body is not None: params['json'] = body

        log = f"post -> {self.endpoint}action/{action} | Params: "
        log += str(params['json']) if 'json' in params else '{}'
        logger.info(log)
        response = requests.post(url, **params) # type: ignore
        data = response.json()
    
        if "error" in data:
            logger.warning(f'{self.endpoint} - {data["error"]["message"]}')
            return {}

        logger.debug('Checking cooldown')
        if "cooldown" in data['data']:
            logger.debug('Parsing cooldown')
            cd = data['data']['cooldown']
            self.cooldown = Cooldown(
                cd['remaining_seconds'],
                datetime.fromisoformat(cd['expiration']),
            )
            
        return data;