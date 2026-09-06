from fastapi import Request, Response
from redis.asyncio.client import Pipeline, Redis  # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

WINDOW_SECONDS = 60
MAX_REQUESTS = 100

class DDOSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        assert request.client is not None
        client_ip = request.client.host
        key = f'rate_limit:{client_ip}'

        redis_client = request.app.state.redis
        assert isinstance(redis_client, Redis)

        async with redis_client.pipeline(transaction=True) as pipe: # type: ignore
            assert isinstance(pipe, Pipeline)
            pipe.incr(key) # type: ignore
            pipe.expire(key, WINDOW_SECONDS, nx=True) # type: ignore
            count, _ = await pipe.execute() # type: ignore

        if count > MAX_REQUESTS:
            return Response("Too Many Requests", status_code=HTTP_429_TOO_MANY_REQUESTS)

        return await call_next(request)