import time

from commons.character import Character
from commons.inventory import Item
from commons.locations import Location, Resource
from dataclass.task import Task

from .role import COOLDOWN, Role


class Gatherer(Role):
    className = 'Gatherer'
    
    def __init__(self, Character: Character) -> None:
        self.tasks = [
            Task('go_to_bank', self.go_to_bank_condition, self.go_to_bank)
        ]
        super().__init__(Character)

    # Conditions
    def go_to_resource_condition(self) -> bool:
        return True
    
    def go_to_bank_condition(self) -> bool:
        return True
    
    async def go_to_bank(self) -> None:
        await self.go_to(Location.BANK)

    # Action
    def _(self) -> None:
        return