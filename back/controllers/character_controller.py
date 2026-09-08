from datetime import UTC, datetime
from typing import Annotated

from core.task_pool import TaskPool
from dto.character import CharacterOut
from dto.inventory import InventoryOut
from fastapi import (
     APIRouter,
     Body,
     HTTPException,
     Request,
)
from fastapi_cache.decorator import cache
from models.character import Character
from pydantic import BaseModel, Field
from roles.cook import Cook
from roles.fisherman import Fisherman
from roles.hunter import Hunter
from roles.lumberjack import Lumberjack
from roles.miner import Miner
from roles.picker import Picker
from roles.role import Role
from starlette.status import *  # type: ignore[reportWildcardImportFromLibrary]

router = APIRouter(prefix='/character', tags=['character'])

Roles: dict[str,type[Role]] = {
    'Cook': Cook,
    'Fisherman': Fisherman,
    'Hunter': Hunter,
    'Lumberjack': Lumberjack,
    'Miner': Miner,
    'Picker': Picker,
}

@router.get('/all')
@cache(expire=60, namespace='CHARACTER')
async def get_characters(request: Request) -> list[CharacterOut]:
     characters: dict[str,Character] = request.app.state.characters
     return [CharacterOut.from_character(c) for c in characters.values()]

@router.get("/{name}/inventory")
@cache(expire=60, namespace='INVENTORY')
async def get_items(name: str, request: Request) -> InventoryOut:
     return InventoryOut.from_inventory(request.app.state.characters[name].inventory)

@router.get("/{name}/logs")
async def get_logs(name: str, request: Request) -> list[str]:
    character = request.app.state.characters.get(name)
    if character is None:
        raise HTTPException(HTTP_404_NOT_FOUND, f"Character '{name}' not found")
    return list(character.logs)

@router.patch('/{name}/rest', status_code=HTTP_202_ACCEPTED)
async def rest(name: str, request: Request):
    state = request.app.state
    pool: TaskPool = state.pool
    character:Character|None = state.characters.get(name)
    if character is None:
        raise HTTPException(HTTP_404_NOT_FOUND, f"Character '{name}' not found")

    # check current routine
    if pool.is_running(name):
        raise HTTPException(HTTP_409_CONFLICT, f"Routine running for '{name}', stop routine before trying again")

    # check cooldown
    if character.cooldown is not None and character.cooldown.expiration >= datetime.now(UTC):
        raise HTTPException(HTTP_409_CONFLICT, f"'{name}' is on cooldown, try again later")
    
    # rest
    await character.rest()

    return {"status": "rested", "character": name}

@router.get('/routines/active')
async def get_active_routines(request: Request) -> list[str]:
    pool: TaskPool = request.app.state.pool
    return pool.active_ids

class RoleIn(BaseModel):
    name:str = Field(description='Role of which to start the routine', min_length=4)

@router.patch("/{name}/routine/start", status_code=HTTP_202_ACCEPTED)
async def start_routine(name: str, role: Annotated[RoleIn, Body()], request: Request):
    state = request.app.state
    pool: TaskPool = state.pool
    character = state.characters.get(name)
    if character is None:
        raise HTTPException(HTTP_404_NOT_FOUND, f"Character '{name}' not found")

    if role.name not in Roles:
        raise HTTPException(HTTP_404_NOT_FOUND, f'Role {role.name} not found')

    # check current routine
    if pool.is_running(name):
        raise HTTPException(HTTP_409_CONFLICT, f"Routine already running for '{name}'")

    # assign routine
    character.role = Roles[role.name](character)
    pool.start(character.name,character.role.routine)

    return {"status": "started", "character": name}

@router.patch("/{name}/routine/stop", status_code=HTTP_202_ACCEPTED)
async def stop_routine(name: str, request: Request):
    state = request.app.state
    pool: TaskPool = state.pool
    character = state.characters.get(name)
    if character is None:
        raise HTTPException(HTTP_404_NOT_FOUND, f"Character '{name}' not found")

    # check current routine
    if not pool.is_running(name):
        raise HTTPException(HTTP_409_CONFLICT, f"No running routine for '{name}'")

    # stop routine
    await pool.stop_and_wait(name)

    return {"status": "stopped", "character": name}