from collections.abc import Callable
from typing import Any

from dataclass.task import Task
from models.character import Character
from models.locations import Location, Workshop

from .role import Role


class Artisan(Role):
    className = 'Artisan'
    
    def __init__(self, Character: Character) -> None:
        self.tasks = [
            Task('go_to_bank', self.go_to_bank_condition, self.go_to_bank),
            Task('go_to_bank', self.withdraw_resources_condition, self.withdraw_raw_food),
            # got to bank
            # retrieve resource
            # check available crafting recipes
            # go to corresponding station
            # craft available recipes
        ]
        super().__init__(Character)

        self.skills: dict[str,dict[str,Any|Callable[[int],bool]]] = {
            'weaponcrafting': {
                'resources': {},
                'crafted': 0,
                'threshold': 10,
                'location': Workshop.WEAPON,
            },
            'gearcrafting': {
                'resources': {},
                'crafted': 0,
                'threshold': 10,
                'location': Workshop.GEAR,
            },
            'jewelrycrafting': {
                'resources': {},
                'crafted': 0,
                'threshold': 10,
                'location': Workshop.JEWELRY,
            },
            'alchemy': {
                'resources': {},
                'crafted': 0,
                'threshold': 20,
                'location': Workshop.ALCHEMY,
            },
        }
        self.skills_iterable = iter(self.skills.items())
        self.current = self.get_next_skill()

    def get_next_skill(self) -> tuple[str,dict[str,Any]]:
        try:
            next_skill = next(self.skills_iterable)
        except StopIteration:
            self.skills_iterable = iter(self.skills.items())
            next_skill = next(self.skills_iterable)
        return next_skill

    # Conditions
    def go_to_bank_condition(self) -> bool:
        return self.withdraw_resources_condition() and self.character.pos != Location.BANK

    def withdraw_resources_condition(self) -> bool:
        return self.bank.is_in_bank(itemtype='resource',skills=[self.current[0]])

    def go_to_station(self) -> bool:
        #if self.character.craftable(self.current[0], )
        return False

    # Actions

    async def withdraw_raw_food(self) -> tuple[bool,bool]:
        success = await self.bank.ask_for_withdraw(self.character, quantity=10, itemtype='resource',skills=[self.current[0]])
        return success, success
