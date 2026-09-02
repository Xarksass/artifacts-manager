import time

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
            Task('withdraw_raw_food', self.withdraw_raw_food_condtion, self.withdraw_raw_food),
            Task('store_cooked_food', self.store_cooked_food_condtion, self.store_cooked_food),
            Task('go_fishing', self.go_fishing_condition, self.go_fishing),
            Task('fishing', self.fishing_condition, self.fishing),
        ]
        super().__init__(Character)

    # Conditions
    def go_to_cooking_condition(self) -> bool:
        return self.cooking_condition() and self.character.pos != Workshop.COOKING

    def cooking_condition(self) -> bool:
        if self.character.inventory.is_full():
            return False
            
        last_attempt = self.cooldowns.get("cooking", 0)
        if (time.monotonic() - last_attempt) < COOLDOWN:
            return False

        raw_food = self.character.inventory.pick(itemtype='resource', subtype=['mob','fishing'])
        if raw_food:
            total_quantity = 0
            for rf in raw_food.values():
                total_quantity += rf.quantity
            return total_quantity >= 10
        return False

    def withdraw_raw_food_condtion(self) -> bool:
        if self.character.inventory.is_full():
            return False
        
        raw_food = self.character.inventory.pick(itemtype='resource', subtype=['mob','fishing'])
        if raw_food:
            return False

        last_attempt = self.cooldowns.get("withdraw_raw_food", 0)
        return (time.monotonic() - last_attempt) >= COOLDOWN

    def store_cooked_food_condtion(self) -> bool:
        return bool(self.character.inventory.pick(itemtype='consumable',subtype=['food']))

    def go_fishing_condition(self) -> bool:
        fish_locations = (FishLocation.BASS,FishLocation.TROUT,FishLocation.SHRIMP,FishLocation.GUDGEON)
        return self.character.pos not in (fish_locations)

    def fishing_condition(self) -> bool:
        return not self.go_fishing_condition()
    
    # Actions
    async def go_to_cooking(self):
        await self.go_to(Workshop.COOKING)

    async def cooking(self):
        raw_food: dict[str,Item]|None = self.character.inventory.pick(itemtype='resource',subtype=['mob','fishing'],skill='cooking')
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
        await self.go_to(Location.BANK)

        bank = Bank()
        success = await bank.ask_for_withdraw(self.character, quantity=10, itemtype='resource',subtype=['mob','fishing'])
        if not success:
            self.cooldowns["withdraw_raw_food"] = time.monotonic()

    async def store_cooked_food(self):
        if self.character.pos != Location.BANK:
            await self.go_to(Location.BANK)
        
        cooked_food: dict[str,Item]|None = self.character.inventory.pick(itemtype='consumable',subtype=['food'])
        if cooked_food:
            bank = Bank()
            for item in cooked_food.values():
                await bank.deposit(self.character,item,item.quantity)

    async def go_fishing(self):
        match self.character.skills.cooking:
            case c if 29 < c:
                destination = FishLocation.BASS
            case c if 19 < c < 30:
                destination = FishLocation.TROUT
            case c if 9 < c < 20:
                destination = FishLocation.SHRIMP
            case _:
                destination = FishLocation.GUDGEON

        await self.go_to(destination)

    async def fishing(self):
        await self.character.gather()
