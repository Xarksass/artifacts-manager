import asyncio
from typing import TYPE_CHECKING

from dataclass.task import Task
from dto.bank import BankOut
from dto.character import CharacterOut
from fastapi_cache import FastAPICache
from models.bank import Bank

from core.logger import get_logger
from core.ws_manager import manager

if TYPE_CHECKING:
    from models.character import Character  # noqa: TC004

logger = get_logger(__name__,'selector')

class Selector:
    def __init__(self, character: Character, tasks: list[Task], stop: asyncio.Event) -> None:
        self.character = character
        self.tasks = tasks
        self.__stop = stop

    async def tick(self) -> bool:
        self.bank = await Bank()
        for task in self.tasks:
            logger.debug(f'Check {task.name} Task: {task.condition()}')

            if task.condition() and not self.__stop.is_set():
                logger.debug(f'Execute Task {task.name}')
                cu, _, bu = await task.action()

                if cu:
                    await FastAPICache.clear(namespace='CHARACTER')
                    await manager.broadcast({
                        "type": "character_update",
                        "data": CharacterOut.from_character(self.character).model_dump(),
                    })

                #if iu:
                #    await FastAPICache.clear(namespace='INVENTORY')
                #    await manager.broadcast({
                #        "type": "inventory_update",
                #        "data": InventoryOut.from_inventory(self.character.inventory).model_dump()
                #    })

                if bu:
                    await FastAPICache.clear(namespace='BANK')
                    await manager.broadcast({
                        "type": "bank_update",
                        "data": BankOut.from_bank(self.bank)
                    })

                return True
        return False
