import time
from collections.abc import Callable
from typing import Any

from commons.bank import Bank
from commons.character import Character
from commons.inventory import Item
from commons.locations import FishLocation, Location, Workshop
from dataclass.task import Task

from .role import COOLDOWN, Role


class Cook(Role):
    className = 'Cook'
    
    def __init__(self, Character: Character) -> None:
        self.tasks = [
            Task('go_to_cooking', self.go_to_cooking_condition, self.go_to_cooking),
            Task('cooking', self.cooking_condition, self.cooking),
            Task('go_to_bank', self.go_to_bank_condition, self.go_to_bank),
            Task('store_cooked_food', self.store_cooked_food_condtion, self.store_cooked_food),
            Task('store_resources', self.store_resources_condtion, self.store_resources),
            Task('withdraw_raw_food', self.withdraw_raw_food_condtion, self.withdraw_raw_food),
            Task('go_fishing', self.go_fishing_condition, self.go_fishing),
            Task('fishing', self.fishing_condition, self.fishing),
        ]
        super().__init__(Character)

        self.fishes: dict[str,dict[str,Any|Callable[[int],bool]]] = {
            'gudgeon': {
                'required': lambda lvl: lvl > 0,
                'gathered': 0,
                'threshold': 20,
                'location': FishLocation.GUDGEON,
            },
            'shrimp': {
                'required': lambda lvl: 9 < lvl < 20,
                'gathered': 0,
                'threshold': 20,
                'location': FishLocation.SHRIMP,
            },
            'trout': {
                'required': lambda lvl: 19 < lvl < 30,
                'gathered': 0,
                'threshold': 20,
                'location': FishLocation.TROUT,
            },
            'boss': {
                'required': lambda lvl: 29 < lvl,
                'gathered': 0,
                'threshold': 20,
                'location': FishLocation.BASS,
            },
        }
        self.fishes_iterable = iter(self.fishes.items())
        self.current = self.get_next_valid_fish()

    def get_next_valid_fish(self) -> tuple[str,dict[str,Any|Callable[[int],bool]]]:
        try:
            next_fish = next(self.fishes_iterable)
            if not next_fish[1]['required'](self.character.skills.fishing):
                self.fishes_iterable = iter(self.fishes.items())
                next_fish = next(self.fishes_iterable)
        except StopIteration:
            self.fishes_iterable = iter(self.fishes.items())
            next_fish = next(self.fishes_iterable)
        return next_fish

    # Conditions
    def go_to_cooking_condition(self) -> bool:
        return self.cooking_condition() and self.character.pos != Workshop.COOKING
    
    def cooking_condition(self) -> bool:
        if self.character.inventory.is_full():
            return False
            
        last_attempt = self.cooldowns.get("cooking", 0)
        if (time.monotonic() - last_attempt) < COOLDOWN:
            return False

        raw_food = self.character.inventory.pick(itemtype='resource', skill='cooking')
        if raw_food:
            total_quantity = 0
            for rf in raw_food.values():
                total_quantity += rf.quantity
            return total_quantity >= 20
        return False

    def go_to_bank_condition(self) -> bool:
        return (self.withdraw_raw_food_condtion() or self.store_cooked_food_condtion() or self.store_resources_condtion()) and self.character.pos != Location.BANK

    def store_cooked_food_condtion(self) -> bool:
        return bool(self.character.inventory.pick(itemtype='consumable',subtype=['food']))

    def store_resources_condtion(self) -> bool:
        return bool(self.character.inventory.pick(itemtype='resource', skill='cooking', exclusion_mode=True))
    
    def withdraw_raw_food_condtion(self) -> bool:
        if self.character.inventory.is_full():
            return False
        
        raw_food = self.character.inventory.pick(itemtype='resource', skill='cooking')
        if raw_food:
            return False

        bank = Bank()
        if not bank.is_in_bank(itemtype='resource',subtype=['mob','fishing']):
            return False

        last_attempt = self.cooldowns.get("withdraw_raw_food", 0)
        return (time.monotonic() - last_attempt) >= COOLDOWN

    def go_fishing_condition(self) -> bool:
        if self.character.inventory.is_full():
            return False
        
        return self.character.pos != self.current[1]['location']

    def fishing_condition(self) -> bool:
        return not self.go_fishing_condition()
    
    # Actions
    async def go_to_cooking(self):
        await self.go_to(Workshop.COOKING)

    async def go_to_bank(self):
        await self.go_to(Location.BANK)

    async def cooking(self):
        raw_food: dict[str,Item]|None = self.character.inventory.pick(itemtype='resource', skill='cooking')
        crafted = 0
        if raw_food:
            for code, item in raw_food.items():
                for recipe in item.crafts['cooking']:
                    craftable = self.character.craftable('cooking',recipe)

                    if not craftable: continue;
                    success = await self.character.craft(recipe.code,craftable)
                    if success:
                        crafted += craftable
                        for code, quantity in recipe.items.items():
                            self.character.inventory.update(code, (quantity * craftable * -1))

        if crafted == 0:
            self.cooldowns["cooking"] = time.monotonic()

    async def withdraw_raw_food(self):
        bank = Bank()
        success = await bank.ask_for_withdraw(self.character, quantity=10, itemtype='resource', skill='cooking')
        if not success:
            self.cooldowns["withdraw_raw_food"] = time.monotonic()

    async def store_cooked_food(self):
        cooked_food: dict[str,Item]|None = self.character.inventory.pick(itemtype='consumable',subtype=['food'])
        if cooked_food:
            bank = Bank()
            item = next(iter(cooked_food.values()))
            await bank.deposit(self.character,item,item.quantity)

    async def store_resources(self):
        resources: dict[str,Item]|None = self.character.inventory.pick(itemtype='resource', skill='cooking', exclusion_mode=True)
        if resources:
            bank = Bank()
            item = next(iter(resources.values()))
            await bank.deposit(self.character,item,item.quantity)
            if self.current[1]['gathered'] >= self.current[1]['threshold']: # type: ignore
                self.current[1]['gathered'] = 0
                self.current = self.get_next_valid_fish()

    async def go_fishing(self):
        #match self.character.skills.fishing:
        #    case c if 29 < c:
        #        destination = FishLocation.BASS
        #    case c if 19 < c < 30:
        #        destination = FishLocation.TROUT
        #    case c if 9 < c < 20:
        #        destination = FishLocation.SHRIMP
        #    case _:
        #        destination = FishLocation.GUDGEON

        await self.go_to(self.current[1]['location']) # type: ignore

    async def fishing(self):
        response = await self.character.gather()
        if len(response):
            for drop in response:
                if drop['code'] == self.current[0]:
                    self.current[1]['gathered'] += drop['quantity']
