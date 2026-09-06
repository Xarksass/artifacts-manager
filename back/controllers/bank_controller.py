from typing import Any

from dto.bank import BankOut
from fastapi import (
    APIRouter,
    Request,
)

#from fastapi.responses import StreamingResponse
from fastapi_cache.decorator import cache
from starlette.status import *  # type: ignore[reportWildcardImportFromLibrary]

router = APIRouter(prefix='/bank', tags=['bank'])

@router.get('/')
@cache(expire=60, namespace='BANK')
async def get_items(request: Request) -> list[dict[str,Any]]:
     return BankOut.from_bank(request.app.state.bank)