from typing import Any, Self, overload

from core.logger import get_logger
from dataclass.item import Item
from endpoints.items import ItemsEndpoint

from models.items import Items

logger = get_logger(__name__,'inventory')


class Inventory(Items):
    total: int = 0
    max_items:int
    api: ItemsEndpoint

    @classmethod
    async def create(cls, content: list[dict[str,Any]], maxi: int = 100) -> Self:
        logger.info("Character's inventory Initialisation ...")
        self = cls()
        self.max_items = maxi
        self.items = await Items.parse_items(ItemsEndpoint(), content)
        self.api = ItemsEndpoint()
        for item in self.items.values():
            self.total += item.quantity
        logger.info("Character's inventory Initialized")
        return self

    @overload
    def pick(self, *, item:str, itemtype:None = None, subtypes:None = None, effects:None = None, skills:None = None, exclusion_mode: bool = False) -> Item | None:...
    @overload
    def pick(self, *, item:None = None, itemtype:str|None = None, subtypes:list[str]|None = None, effects:list[str]|None = None, skills:list[str]|None = None, exclusion_mode: bool = False) -> dict[str, Item]:...
    def pick(self, *, item: str | None = None, itemtype: str | None = None, subtypes: list[str] | None = None, effects: list[str] | None = None, skills: list[str] | None = None, exclusion_mode: bool = False) -> dict[str, Item] | Item | None:
        if item is not None:
            return super().get(self.items, item=item, exclusion_mode=exclusion_mode)
        else:
            return super().get(self.items, itemtype=itemtype, subtypes=subtypes, effects=effects, skills=skills, exclusion_mode=exclusion_mode)

    def is_full(self) -> bool:
        return self.total >= self.max_items

    async def add(self, item:str, quantity:int):
        self.total += quantity
        return await super().update(self.api, self.items, item, quantity, 'INVENTORY')

    async def remove(self, item:str, quantity:int):
        self.total -= quantity
        return await super().update(self.api, self.items, item, (quantity * -1), 'INVENTORY')
        