from dataclass.item import Item, ResourceType
from dataclass.location import Position
from dataclass.task import Task
from models.character import Character
from models.locations import Location, Resource, Workshop

from roles.role import Role


class Miner(Role):
    className = 'Miner'
    resources: dict[str,ResourceType]
    current: ResourceType
    workshop: Position = Workshop.FORGE
    
    def __init__(self, Character: Character) -> None:
        self.tasks = [
            Task('go_to_resource', self.go_to_resource_condition, self.go_to_resource),
            Task('gather_resource', self.gather_resource_condition, self.gather_resource),
            #Task('got_to_workshop', self.go_to_workshop_condition, self.go_to_workshop),
            #Task('craft_resources', self.craft_resources_condition, self.craft_resources),
            Task('go_to_bank', self.go_to_bank_condition, self.go_to_bank),
            Task('store_resources', self.store_resources_condition, self.store_resources),
        ]
        super().__init__(Character)

        self.resources = {
            'copper': ResourceType(
                code = 'copper_ore',
                required = lambda lvl: lvl > 0,
                gathered = 0,
                threshold = 100,
                location = Resource.COPPER,
            ),
            'iron': ResourceType(
                code = 'iron_ore',
                required = lambda lvl: 9 < lvl,
                gathered = 0,
                threshold = 100,
                location = Resource.IRON,
            ),
            'coal': ResourceType(
                code = 'coal',
                required = lambda lvl: 19 < lvl,
                gathered = 0,
                threshold = 100,
                location = Resource.COAL,
            ),
        }

        self.resources_iterable = iter(self.resources.values())
        self.current = self._get_next_valid_resource()

    def _reset_resource_iterable(self) -> ResourceType:
        self.resources_iterable = iter(self.resources.values())
        return next(self.resources_iterable)

    def _get_next_valid_resource(self) -> ResourceType:
        try:
            next_resource = next(self.resources_iterable)
            if not next_resource.required(self.character.skills.mining):
                next_resource = self._reset_resource_iterable()
        except StopIteration:
            next_resource = self._reset_resource_iterable()
        return next_resource

    def _threshold_reached(self) -> bool:
        return self.current.gathered >= self.current.threshold

    # Conditions
    def go_to_resource_condition(self) -> bool:
        return self.gather_resource_condition() and self.character.pos != self.current.location

    def gather_resource_condition(self) -> bool:
        if self.character.inventory.is_full():
            return False

        return not self._threshold_reached()
    
    def go_to_workshop_condition(self) -> bool:
        return self.craft_resources_condition() and self.character.pos != self.workshop

    def craft_resources_condition(self) -> bool:
        return self.character.inventory.is_full() or self._threshold_reached()
    
    def go_to_bank_condition(self) -> bool:
        return self.store_resources_condition() and self.character.pos != Location.BANK
    
    def store_resources_condition(self) -> bool:
        #return bool(self.character.inventory.pick(itemtype='resource', subtypes=['bar'])) or self.character.inventory.is_full()
        return self._threshold_reached() or self.character.inventory.is_full()

    # Action
    # Go to gather resource
    async def go_to_resource(self) -> tuple[bool,bool]:
        return await self.go_to(self.current.location)

    async def gather_resource(self) -> tuple[bool,bool]:
        response = await self.character.gather()
        if response:
            for drop in response:
                if drop['code'] == self.current.code:
                    self.current.gathered += drop['quantity']
        return bool(response), False

    # go to workshop to craft once threshold is reached or inventory is full
    async def go_to_workshop(self) -> tuple[bool,bool]:
        return await self.go_to(self.workshop)

    async def craft_resources(self) -> tuple[bool,bool]:
        # check current ressource craft recipe
        ore: Item|None = self.character.inventory.pick(item=self.current.code)
        crafted = 0
        if ore is not None and ore.quantity > 0:
            for recipe in ore.crafts['mining']:
                craftable = self.character.craftable('mining',recipe)
                if not craftable: continue;

                # create resource
                success = await self.character.craft(recipe,craftable)
                if success:
                    crafted = craftable
                    break
        return bool(crafted), False

    # Store items once created
    async def store_resources(self) -> tuple[bool,bool]:
        success = False
        """ resources = self.character.inventory.pick(itemtype='resource', subtypes=['bar'])
        if resources:
            to_store: list[dict[str,str|int]] = []
            for resource in resources.values():
                to_store.append({'code': resource.code, 'quantity': resource.quantity})
            success = await self.bank.deposit(self.character, items=to_store) """
        resources = self.character.inventory.pick(itemtype='resource')
        if resources:
            to_store: list[dict[str,str|int]] = []
            for resource in resources.values():
                to_store.append({'code': resource.code, 'quantity': resource.quantity})

            success = await self.bank.deposit(self.character, items=to_store)
        return success, success