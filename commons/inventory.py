from dataclasses import dataclass
from typing import Any, overload

from commons.items import Items
from dataclass.item import Item
from endpoints.items import ItemsEndpoint


@dataclass
class Slot:
    item: str
    quantity: int

class Inventory(Items):
    total: int = 0
    max_items:int
    api: ItemsEndpoint

    def __init__(self, content: list[dict[str,Any]], maxi: int = 100) -> None:
        self.max_items = maxi
        self.items = Items.parse_items(ItemsEndpoint(), content)
        self.api = ItemsEndpoint()

    @overload
    def pick(self, *, item:str, itemtype:None = None, subtype:None = None, effect:None = None, skill:None = None) -> Item | None:...
    @overload
    def pick(self, *, item:None = None, itemtype:str|None = None, subtype:list[str]|None = None, effect:str|None = None, skill:str|None = None) -> dict[str, Item]:...
    def pick(self, *, item: str | None = None, itemtype: str | None = None, subtype: list[str] | None = None, effect: str | None = None, skill: str | None = None) -> dict[str, Item] | Item | None:
        if item is not None:
            return super().get(self.items, item=item)
        else:
            return super().get(self.items, itemtype=itemtype, subtype=subtype, effect=effect, skill=skill)

    def is_full(self) -> bool:
        return self.total >= self.max_items
    
    def update(self, item:str, quantity:int) -> None:
        stored = self.items.get(item)

        if stored is None:
            if quantity < 0:
                return
            item_data = self.api.get(item)
            if item_data:
                self.items[item_data['code']] = Item(
                    item_data['name'], 
                    item_data['code'], 
                    item_data['level'], 
                    item_data['type'], 
                    item_data['subtype'], 
                    item_data['conditions'], 
                    {effect['code']:effect['value'] for effect in item_data['effects']}, 
                    item_data['craft'], 
                    item_data['tradeable'], 
                    item_data['recyclable'], 
                    quantity
                )
                self.total += quantity
        else:
            self.total += quantity - stored.quantity
            stored.quantity += quantity