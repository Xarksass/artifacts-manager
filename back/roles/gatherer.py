from models.character import Character
from models.locations import Place
from schemas.item import ResourceType
from schemas.task import Task

from roles.role import Role


class Gatherer(Role):
    className = 'Gatherer'
    resources: dict[str,ResourceType]
    current: ResourceType
    skill: str

    def __init__(self, Character: Character) -> None:
        self.tasks = [
            Task('Go to resource', 'go_to_resource', self.go_to_resource_condition, self.go_to_resource),
            Task('Gather resources', 'gather_resource', self.gather_resource_condition, self.gather_resource),
            Task('Go to bank', 'go_to_bank', self.go_to_bank_condition, self.go_to_bank),
            Task('Store resources', 'store_resources', self.store_resources_condition, self.store_resources),
        ]

        super().__init__(Character)

        self.resources_iterable = iter(self.resources.values())
        self.current = self._get_next_valid_resource()

    def _reset_resource_iterable(self) -> ResourceType:
        self.resources_iterable = iter(self.resources.values())
        return next(self.resources_iterable)

    def _get_next_valid_resource(self) -> ResourceType:
        try:
            next_resource = next(self.resources_iterable)
            if not next_resource.required(getattr(self.character.skills, self.skill)):
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
    
    def go_to_bank_condition(self) -> bool:
        return self.store_resources_condition() and self.character.pos != Place.BANK
    
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

    # Store items once created
    async def store_resources(self) -> tuple[bool,bool]:
        success = False
        resources = self.character.inventory.pick(itemtype='resource')
        if resources:
            to_store: list[dict[str,str|int]] = []
            for code, quantity in resources.items():
                to_store.append({'code': code, 'quantity': quantity})

            success = await self.bank.deposit(self.character, items=to_store)
            if success:
                self.current.gathered = 0
                self.current = self._get_next_valid_resource()
        return success, success