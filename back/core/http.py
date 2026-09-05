# core/http.py
from __future__ import annotations

import os
from typing import Any

import httpx

_client: httpx.AsyncClient | None = None

def init_client(**kwargs: Any) -> httpx.AsyncClient:
    global _client
    default_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['TOKEN']}",
    }
    _client = httpx.AsyncClient(headers=default_headers, **kwargs)
    return _client

async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None

def get_client() -> httpx.AsyncClient:
    if _client is None:
        raise RuntimeError("HTTP client not initialised — init_client() called in lifespan")
    return _client