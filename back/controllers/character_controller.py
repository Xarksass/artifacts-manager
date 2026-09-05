#from decorators.invalidate_cache_decorator import invalidate_cache
#from dto.requests.task_dto import EditTaskDto, ExportTaskDto, ListTaskDto, TaskDto
#from dto.responses import tasklist_dto as TaskList
from core.task_pool import TaskPool
from dto.character import CharacterOut
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

#from fastapi.responses import StreamingResponse
from fastapi_cache.decorator import cache
from models.character import Character
from roles.cook import Cook
from roles.gatherer import Gatherer
from roles.hunter import Hunter
from roles.role import Role
from starlette.status import *  # type: ignore[reportWildcardImportFromLibrary]

router = APIRouter(prefix='/character', tags=['character'])

Roles: dict[str,type[Role]] = {
    'Hunter': Hunter,
    'Cook': Cook,
    'Gatherer': Gatherer,
}

@router.get('/all')
@cache(expire=60, namespace='CHARACTER')
async def get_characters(request: Request) -> list[CharacterOut]:
     characters: dict[str,Character] = request.app.state.characters
     return [CharacterOut.from_character(c) for c in characters.values()]

@router.patch("/{name}/routine", status_code=202)
async def start_routine(name: str, request: Request):
    state = request.app.state
    pool: TaskPool = state.pool
    character = state.characters.get(name)
    if character is None:
        raise HTTPException(404, f"Character '{name}' not found")

    # check current routine
    if pool.is_running(name):
        raise HTTPException(409, f"Routine already running for '{name}'")

    # assign routine
    character.role = Roles['Hunter'](character)
    pool.start(character.name,character.role.routine)

    return {"status": "started", "character": name}