import asyncio
import time
from typing import TYPE_CHECKING

from core.logger import get_logger
from core.selector import Selector
from models.bank import Bank

#from models.inventory import Inventory
from models.locations import Place, Position
from schemas.task import Task

if TYPE_CHECKING:
    from models.character import Character  # noqa: TC004

COOLDOWN = 300

logger = get_logger(__name__,'role')

class Role:
    className:str = 'Peasant'
    tasks: list[Task]|None = None
    priority_tasks:asyncio.Queue[Task]
    cooldowns: dict[str,float]
    bank: Bank
    __stop: asyncio.Event = asyncio.Event()

    def __init__(self, Character: Character) -> None:
        super().__init__()
        self.character = Character
        self.cooldowns = {}
        self.priority_tasks = asyncio.Queue()
        if self.tasks is not None:
            self.selector = Selector(self.character, self.tasks, self.__stop, self.priority_tasks)

    # Actions
    async def go_to_bank(self) -> tuple[bool,bool]:
        return await self.go_to(Place.BANK)

    # Class Methods
    def set_task_cooldown(self, task:str):
        self.cooldowns[task] = time.monotonic()

    async def go_to(self, location: Position) -> tuple[bool,bool]:
        await self.character.move_to(location.x, location.y)
        return False, False

    async def stop_routine(self) -> None:
        logger.info(f'Stop routine called for {self.character.name}')
        self.__stop.set()

    async def routine(self, stop_event: asyncio.Event) -> None:
        logger.info(f'Starting {self.className} routine for {self.character.name}')
        self.bank = Bank.open()
        loop = asyncio.get_running_loop()

        while not stop_event.is_set():
            deadline = self.character.next_ready_at()

            if deadline is not None:
                remaining = deadline - loop.time()
                if remaining >= 0:
                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=remaining)
                        # stop_event set avant la fin du cooldown -> on sort proprement
                        break
                    except TimeoutError:
                        pass  # cooldown écoulé naturellement, on continue
            
            if stop_event.is_set():
                break

            if not await self.selector.tick():
                break