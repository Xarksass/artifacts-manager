from typing import Any

from commons.bank import Bank
from commons.character import Character
from commons.locations import Location, Resource
from dataclass.task import Task

from .role import Role


class Gatherer(Role):
    className = 'Gatherer'
    resources: dict[str,Any]
    
    def __init__(self, Character: Character) -> None:
        self.resources = {
            'sunflower': {
                'gathered': 0,
                'threshold': 100,
                'location': Resource.SUNFLOWER,
            },
            'ash_wood': {
                'gathered': 0,
                'threshold': 100,
                'location': Resource.ASH,
            },
            'copper_ore': {
                'gathered': 0,
                'threshold': 100,
                'location': Resource.COPPER,
            },
        }
        self.resources_iterable = iter(self.resources.items())
        self.current = next(self.resources_iterable)
        self.tasks = [
            Task('go_to_resource', self.go_to_resource_condition, self.go_to_resource),
            Task('gather_resource', self.gather_resource_condition, self.gather_resource),
            Task('go_to_bank', self.go_to_bank_condition, self.go_to_bank),
            Task('store_resources', self.store_resources_condition, self.store_resources),
        ]
        super().__init__(Character)

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
    async def go_to_resource(self):
        await self.go_to(self.current[1]['location'])

    async def gather_resource(self):
        response = await self.character.gather()
        if response:
            for drop in response:
                if drop['code'] == self.current[0]:
                    self.current[1]['gathered'] += drop['quantity']

    async def go_to_bank(self):
        await self.go_to(Location.BANK)

    async def store_resources(self):
        if self.character.pos != Location.BANK:
            await self.go_to(Location.BANK)
        
        resources = self.character.inventory.pick(itemtype='resource')
        if resources:
            bank = Bank()
            item = next(iter(resources.values()))
            await bank.deposit(self.character,item,item.quantity)
            if self.current[1]['gathered'] >= self.current[1]['threshold']:
                self.current[1]['gathered'] = 0
                try:
                    self.current = next(self.resources_iterable)
                except StopIteration:
                    self.resources_iterable = iter(self.resources.items())
                    self.current = next(self.resources_iterable)