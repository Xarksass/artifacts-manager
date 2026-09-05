#from decorators.invalidate_cache_decorator import invalidate_cache

#from dto.requests.task_dto import EditTaskDto, ExportTaskDto, ListTaskDto, TaskDto
#from dto.responses import tasklist_dto as TaskList
from dto.bank import BankOut
from dto.item import ItemOut
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
async def get_items(request: Request) -> list[ItemOut]:
     return BankOut.from_bank(request.app.state.bank)