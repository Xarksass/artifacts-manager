import time
from collections.abc import Callable
from typing import Any

from core.logger import get_logger
from dataclass.task import Task
from models.character import Character
from models.inventory import Item
from models.locations import FishLocation, Location, Workshop

from roles.role import COOLDOWN, Role

logger = get_logger(__name__,'cook')


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

        raw_food = self.character.inventory.pick(itemtype='resource', skills=['cooking'])
        if raw_food:
            total_quantity = 0
            for rf in raw_food.values():
                total_quantity += rf.quantity
            return total_quantity >= 20
        return False

    def go_to_bank_condition(self) -> bool:
        return (self.withdraw_raw_food_condtion() or self.store_cooked_food_condtion() or self.store_resources_condtion()) and self.character.pos != Location.BANK

    def store_cooked_food_condtion(self) -> bool:
        return bool(self.character.inventory.pick(itemtype='consumable', subtypes=['food']))

    def store_resources_condtion(self) -> bool:
        return bool(self.character.inventory.pick(itemtype='resource', skills=['cooking'], exclusion_mode=True)) and self.character.inventory.is_full()
    
    def withdraw_raw_food_condtion(self) -> bool:
        if self.character.inventory.is_full():
            return False
        
        raw_food = self.character.inventory.pick(itemtype='resource', skills=['cooking'])
        if raw_food:
            return False

        return self.bank.is_in_bank(itemtype='resource',subtypes=['mob','fishing'])

    def go_fishing_condition(self) -> bool:
        return self.fishing_condition() and self.character.pos != self.current[1]['location']

    def fishing_condition(self) -> bool:
        return not self.character.inventory.is_full()
    
    # Actions
    async def go_to_cooking(self) -> tuple[bool,bool]:
        return await self.go_to(Workshop.COOKING)

    async def cooking(self) -> tuple[bool,bool]:
        logger.debug('cooking...')
        raw_food: dict[str,Item]|None = self.character.inventory.pick(itemtype='resource', skills=['cooking'])
        crafted = 0
        if raw_food:
            for ingredient in raw_food.values():
                for recipe in ingredient.crafts['cooking']:
                    craftable = self.character.craftable('cooking',recipe)
                    if not craftable: continue;
                    success = await self.character.craft(recipe,craftable)
                    if success:
                        crafted = craftable
                        break
                if crafted: break
            return True, False
        if crafted == 0:
            self.cooldowns["cooking"] = time.monotonic()
        return False, False

    async def withdraw_raw_food(self) -> tuple[bool,bool]:
        await self.bank.ask_for_withdraw(self.character, quantity=10, itemtype='resource', skills=['cooking'])
        return True, True

    async def store_cooked_food(self) -> tuple[bool,bool]:
        cooked_food: dict[str,Item]|None = self.character.inventory.pick(itemtype='consumable',subtypes=['food'])
        if cooked_food:
            to_store: list[dict[str,str|int]] = []
            for food in cooked_food.values():
                to_store.append({'code': food.code, 'quantity': food.quantity})

            await self.bank.deposit(self.character, items=to_store)
            return True, True
        return False, False

    async def store_resources(self) -> tuple[bool,bool]:
        resources: dict[str,Item]|None = self.character.inventory.pick(itemtype='resource', skills=['cooking'], exclusion_mode=True)
        if resources:
            to_store: list[dict[str,str|int]] = []
            for resource in resources.values():
                to_store.append({'code': resource.code, 'quantity': resource.quantity})

            await self.bank.deposit(self.character, items=to_store)
            return True, True
        return False, False

    async def go_fishing(self) -> tuple[bool,bool]:
        return await self.go_to(self.current[1]['location']) # type: ignore

    async def fishing(self) -> tuple[bool,bool]:
        response = await self.character.gather()
        if len(response):
            for drop in response:
                if drop['code'] == self.current[0]:
                    self.current[1]['gathered'] += drop['quantity']
                    if self.current[1]['gathered'] >= self.current[1]['threshold']: # type: ignore
                        self.current[1]['gathered'] = 0
                        self.current = self.get_next_valid_fish()
            return True, False
        return False, False
