from core.logger import get_logger
from dataclass.task import Task
from models.character import Character
from models.locations import Location, Monster

from roles.role import Role

logger = get_logger(__name__,'hunter')


class Hunter(Role):
    className = 'Hunter'
    
    def __init__(self, Character: Character) -> None:
        self.tasks = [
            Task('go_to_bank', self.go_to_bank_condition, self.go_to_bank),
            Task('withdraw_heal_item', self.withdraw_heal_item_condition, self.withdraw_heal_item),
            Task('heal', self.heal_condition, self.heal),
            Task('find_chicken', self.find_chicken_condition, self.find_chicken),
            Task('kill_chicken', self.kill_chicken_condition, self.kill_chicken),
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
        logger.debug('--- find_chicken_condition ---')
        logger.debug(f'self.kill_chicken_condition() = {self.kill_chicken_condition()}')
        logger.debug(f'self.character.pos({self.character.pos}) != Monster.CHICKEN({Monster.CHICKEN}) = {self.character.pos != Monster.CHICKEN}')
        return self.kill_chicken_condition() and self.character.pos != Monster.CHICKEN
    
    def kill_chicken_condition(self) -> bool:
        logger.debug('--- kill_chicken_condition ---')
        logger.debug(f"self.character.inventory.is_full() = {self.character.inventory.is_full()}")
        if self.character.inventory.is_full():
            return False
        
        logger.debug(f"self.character.inventory.pick(item='raw_chicken') = {bool(self.character.inventory.pick(item='raw_chicken'))}")
        raw_chicken = self.character.inventory.pick(item='raw_chicken')
        if raw_chicken is not None:
            return raw_chicken.quantity < 20
        return True
    
    def go_to_bank_condition(self) -> bool:
        logger.debug('--- go_to_bank_condition ---')
        logger.debug(f"self.withdraw_heal_item_condition() = {self.withdraw_heal_item_condition()}")
        logger.debug(f"self.store_resources_condition() = {self.store_resources_condition()}")
        logger.debug(f"self.character.pos != Location.BANK = {self.character.pos != Location.BANK}")
        return (self.withdraw_heal_item_condition() or self.store_resources_condition()) and self.character.pos != Location.BANK
    
    def withdraw_heal_item_condition(self) -> bool:
        logger.debug('--- withdraw_heal_item_condition ---')
        logger.debug(f"self.character.inventory.is_full() = {self.character.inventory.is_full()}")
        if self.character.inventory.is_full():
            return False

        logger.debug(f"self.character.inventory.pick(itemtype='consumable',effects=['heal']) = {bool(self.character.inventory.pick(itemtype='consumable',effects=['heal']))}")
        if self.character.inventory.pick(itemtype='consumable',effects=['heal']):
            return False

        logger.debug(f"bank.is_in_bank(itemtype='consumable',effects=['heal']) = {self.bank.is_in_bank(itemtype='consumable',effects=['heal'])}")
        return self.bank.is_in_bank(itemtype='consumable',effects=['heal'])
    
    def store_resources_condition(self) -> bool:
        logger.debug('--- store_resources_condition ---')
        resources = self.character.inventory.pick(itemtype='resource')
        if self.character.inventory.is_full() and resources:
            return True

        if resources:
            total = sum([r.quantity for r in resources.values()])
            return total >= 20
        return False

    # Actions
    async def heal(self) -> tuple[bool,bool,bool]:
        await self.character.heal()
        return True, False, False 

    async def find_chicken(self) -> tuple[bool,bool,bool]:
        await self.character.move_to(Monster.CHICKEN.x, Monster.CHICKEN.y)
        return True, False, False 

    async def kill_chicken(self) -> tuple[bool,bool,bool]:
        await self.character.fight()
        return True, True, False

    async def store_resources(self) -> tuple[bool,bool,bool]:
        resources = self.character.inventory.pick(itemtype='resource')
        if resources:
            to_store: list[dict[str,str|int]] = []
            for resource in resources.values():
                to_store.append({'code': resource.code, 'quantity': resource.quantity})

            await self.bank.deposit(self.character, items=to_store)
            return False, True, True
        return False, False, False

    async def withdraw_heal_item(self) -> tuple[bool,bool,bool]:
        await self.bank.ask_for_withdraw(self.character, quantity=5, itemtype='consumable', effects=['heal'])
        return False, True, True