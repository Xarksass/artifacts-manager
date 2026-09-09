import time

from core.logger import get_logger
from models.character import Character
from models.grimoire import Grimoire
from models.locations import Place, Workshop
from schemas.task import Task

from roles.role import COOLDOWN, Role

logger = get_logger(__name__,'cook')


class Cook(Role):
    className = 'Cook'
    
    def __init__(self, Character: Character) -> None:
        self.tasks = [
            Task('Go to cooking station', 'go_to_cooking', self.go_to_cooking_condition, self.go_to_cooking),
            Task('Cook food', 'cooking', self.cooking_condition, self.cooking),
            Task('Go to bank', 'go_to_bank', self.go_to_bank_condition, self.go_to_bank),
            Task('Store cooked food', 'store_cooked_food', self.store_cooked_food_condtion, self.store_cooked_food),
            Task('Store resources', 'store_resources', self.store_resources_condtion, self.store_resources),
            Task('Withdraw raw food', 'withdraw_raw_food', self.withdraw_raw_food_condtion, self.withdraw_raw_food),
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

        raw_food = self.character.inventory.pick(itemtype='resource', skills=['cooking'])
        if raw_food:
            total_quantity = 0
            for rf in raw_food.values():
                total_quantity += rf
            return total_quantity >= 20
        return False

    def go_to_bank_condition(self) -> bool:
        return (self.withdraw_raw_food_condtion() or self.store_cooked_food_condtion() or self.store_resources_condtion()) and self.character.pos != Place.BANK

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

        return self.bank.is_in_bank(itemtype='resource', skills=['cooking'])
    
    # Actions
    async def go_to_cooking(self) -> tuple[bool,bool]:
        return await self.go_to(Workshop.COOKING)

    async def cooking(self) -> tuple[bool,bool]:
        logger.debug('cooking...')
        raw_food: dict[str,int]|None = self.character.inventory.pick(itemtype='resource', skills=['cooking'])
        crafted = 0
        if raw_food:
            _grimoire = Grimoire.open()
            for ingredient in raw_food:
                cooking_recipes = _grimoire.recipes.get('cooking', [])
                for recipe in cooking_recipes:
                    if ingredient in recipe.items:
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
        cooked_food: dict[str,int]|None = self.character.inventory.pick(itemtype='consumable',subtypes=['food'])
        if cooked_food:
            to_store: list[dict[str,str|int]] = []
            for code, quantity in cooked_food.items():
                to_store.append({'code': code, 'quantity': quantity})

            await self.bank.deposit(self.character, items=to_store)
            return True, True
        return False, False

    async def store_resources(self) -> tuple[bool,bool]:
        resources: dict[str,int]|None = self.character.inventory.pick(itemtype='resource', skills=['cooking'], exclusion_mode=True)
        if resources:
            to_store: list[dict[str,str|int]] = []
            for code, quantity in resources.items():
                to_store.append({'code': code, 'quantity': quantity})

            await self.bank.deposit(self.character, items=to_store)
            return True, True
        return False, False
