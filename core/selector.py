import asyncio

from core.logger import get_logger
from dataclass.task import Task

logger = get_logger(__name__,'selector')

class Selector:
    def __init__(self, tasks: list[Task], stop: asyncio.Event) -> None:
        self.tasks = tasks
        self.__stop = stop

    async def tick(self) -> bool:
        for task in self.tasks:
            logger.debug(f'Check {task.name} Task: {task.condition()}')
            if task.condition() and not self.__stop.is_set():
                logger.debug(f'Execute Task {task.name}')
                await task.action()
                return True
        return False
