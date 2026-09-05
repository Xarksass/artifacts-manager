from typing import Any

from dataclass.task import Task
from models.character import Character
from models.locations import Location, Resource

from roles.role import Role


class Gatherer(Role):
    className = 'Gatherer'
    resources: dict[str,Any]
    
    def __init__(self, Character: Character) -> None:
        self.tasks = [
            Task('go_to_resource', self.go_to_resource_condition, self.go_to_resource),
            Task('gather_resource', self.gather_resource_condition, self.gather_resource),
            Task('go_to_bank', self.go_to_bank_condition, self.go_to_bank),
            Task('store_resources', self.store_resources_condition, self.store_resources),
        ]
        super().__init__(Character)
        self.resources = {
            'sunflower': {
                'gathered': 0,
                'threshold': 10,
                'location': Resource.SUNFLOWER,
            },
            'ash_wood': {
                'gathered': 0,
                'threshold': 10,
                'location': Resource.ASH,
            },
            'copper_ore': {
                'gathered': 0,
                'threshold': 10,
                'location': Resource.COPPER,
            },
        }
        self.resources_iterable = iter(self.resources.items())
        self.current = next(self.resources_iterable)

    # Conditions
    def go_to_resource_condition(self) -> bool:
        return self.gather_resource_condition() and self.character.pos != self.current[1]['location']

    def gather_resource_condition(self) -> bool:
        if self.character.inventory.is_full():
            return False

        if self.current[1]['gathered'] >= self.current[1]['threshold']:
            return False

        current_resource = self.character.inventory.pick(item=self.current[0])
        return not current_resource or self.current[1]['gathered'] < self.current[1]['threshold']
    
    def go_to_bank_condition(self) -> bool:
        return self.store_resources_condition() and self.character.pos != Location.BANK
    
    def store_resources_condition(self) -> bool:
        return bool(self.character.inventory.pick(itemtype='resource'))

    # Action
    async def go_to_resource(self) -> tuple[bool,bool,bool]:
        return await self.go_to(self.current[1]['location'])

    async def gather_resource(self) -> tuple[bool,bool,bool]:
        response = await self.character.gather()
        if response:
            for drop in response:
                if drop['code'] == self.current[0]:
                    self.current[1]['gathered'] += drop['quantity']
                    if self.current[1]['gathered'] >= self.current[1]['threshold']:
                        self.current[1]['gathered'] = 0
                        try:
                            self.current = next(self.resources_iterable)
                        except StopIteration:
                            self.resources_iterable = iter(self.resources.items())
                            self.current = next(self.resources_iterable)
            return False, True, False
        return False, False, False

    async def store_resources(self) -> tuple[bool,bool,bool]:
        if self.character.pos != Location.BANK:
            await self.go_to(Location.BANK)
        
        resources = self.character.inventory.pick(itemtype='resource')
        if resources:
            to_store: list[dict[str,str|int]] = []
            for resource in resources.values():
                to_store.append({'code': resource.code, 'quantity': resource.quantity})

            await self.bank.deposit(self.character, items=to_store)
            return False, True, True
        return False, False, False