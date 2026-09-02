import time

from commons.bank import Bank
from commons.character import Character
from commons.locations import Location, Monster
from dataclass.task import Task

from .role import COOLDOWN, Role


class Hunter(Role):
    className = 'Hunter'
    
    def __init__(self, Character: Character) -> None:
        self.tasks = [
            Task('heal', self.heal_condition, self.heal),
            Task('find_chicken', self.find_chicken_condition, self.find_chicken),
            Task('kill_chicken', self.kill_chicken_condition, self.kill_chicken),
            Task('go_to_bank', self.go_to_bank_condition, self.go_to_bank),
            Task('withdraw_heal_item', self.withdraw_heal_item_condition, self.withdraw_heal_item),
            Task('store_resources', self.store_resources_condition, self.store_resources),
        ]
        super().__init__(Character)

    # Conditions
    def heal_condition(self) -> bool:
        return self.character.hp <= (self.character.max_hp * 0.45)

    #def find_monster_condition(self) -> bool:
    #    if not hunt_monster_condition():
    #        return False

    #def hunt_monster_condition(self) -> bool:
    #    if self.character.inventory.is_full():
    #        return False
    #    # check inventory for targeted monster

    
    def find_chicken_condition(self) -> bool:
        return self.kill_chicken_condition() and self.character.pos != Monster.CHICKEN
    
    def kill_chicken_condition(self) -> bool:
        if self.character.inventory.is_full():
            return False
        
        raw_chicken = self.character.inventory.pick(item='raw_chicken')
        if raw_chicken is not None:
            return raw_chicken.quantity < 10
        return True
    
    def go_to_bank_condition(self) -> bool:
        return (self.withdraw_heal_item_condition() or self.store_resources_condition) and self.character.pos != Location.BANK
    
    def withdraw_heal_item_condition(self) -> bool:
        if self.character.inventory.is_full():
            return False

        if self.character.inventory.pick(itemtype='consumable',effect='heal'):
            return False;

        bank = Bank()
        if not bank.is_in_bank(itemtype='consumable',effect='heal'):
            return False

        last_attempt = self.cooldowns.get("withdraw_heal_item", 0)
        return time.monotonic() - last_attempt >= COOLDOWN 
    
    def store_resources_condition(self) -> bool:
        return True

    # Actions
    async def heal(self):
        await self.character.heal()

    async def find_chicken(self):
        await self.character.move_to(Monster.CHICKEN.x, Monster.CHICKEN.y)

    async def kill_chicken(self):
        await self.character.fight()

    async def go_to_bank(self):
        await self.go_to(Location.BANK)

    async def store_resources(self):
        resources = self.character.inventory.pick(itemtype='resource')
        if resources:
            bank = Bank()
            item = next(iter(resources.values()))
            await bank.deposit(self.character,item,item.quantity)

    async def withdraw_heal_item(self):
        bank = Bank()
        success = await bank.ask_for_withdraw(self.character, quantity=10, itemtype='consumable',effect='heal')
        if not success:
            self.cooldowns["withdraw_heal_item"] = time.monotonic()