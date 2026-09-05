import functools
from collections.abc import Callable
from typing import Any

from fastapi_cache import FastAPICache


def invalidate_cache(namespace: str):
    def decorator(f: Callable[...,Any]):
        @functools.wraps(f)
        async def inner(*args: tuple[Any], **kwargs: dict[str,Any]):
            await f(*args, **kwargs)
            await FastAPICache.clear(namespace=namespace)
        return inner
    return decorator