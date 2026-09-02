from abc import ABC
from typing import Any, overload

from dataclass.item import Item, Recipe
from endpoints.items import ItemsEndpoint


class Items(ABC):
    items: dict[str,Item]

    @staticmethod
    def parse_items(api: ItemsEndpoint, items: list[dict[str,Any]]) -> dict[str,Item]:
        parsed_items: dict[str,Item] = {}
        for item in items:
            item_data = api.fetch(item['code'])
            if item_data:
                craft_list = api.search(item_data['code'])
                crafts: dict[str,list[Recipe]] = {}
                
                for craftable in craft_list:
                    craft = craftable['craft']
                    recipe_list = crafts.setdefault(craft['skill'],[])
                    recipe_list.append(Recipe(
                        craftable['code'],
                        craft['skill'],
                        craft['level'],
                        {bi['code']:bi['quantity'] for bi in craft['items']},
                        craft['quantity']
                    ))

                for key, recipe_list in crafts.items():
                    crafts[key] = sorted(recipe_list, key=lambda x: (x.level *-1))
                
                parsed_items[item_data['code']] = Item(
                    item_data['name'], 
                    item_data['code'], 
                    item_data['level'], 
                    item_data['type'], 
                    item_data['subtype'], 
                    item_data['conditions'], 
                    {effect['code']:effect['value'] for effect in item_data['effects']}, 
                    crafts, 
                    item_data['tradeable'], 
                    item_data['recyclable'], 
                    item['quantity']
                )
        return parsed_items
    
    @overload
    @staticmethod
    def get(items:dict[str,Item], *, item: str, itemtype: None = None, subtype: None = None, effect: None = None, skill: None = None, exclusion_mode: bool = False) -> Item | None: ...
    @overload
    @staticmethod
    def get(items:dict[str,Item], *, item: None = None, itemtype: str | None = None, subtype: list[str] | None = None, effect: str | None = None, skill: str | None = None, exclusion_mode: bool = False) -> dict[str, Item] | None: ...
    @staticmethod
    def get(items:dict[str,Item], *, 
            item: str | None = None, 
            itemtype: str | None = None, 
            subtype: list[str] | None = None, 
            effect: str | None = None, 
            skill: str | None = None,
            exclusion_mode: bool = False) -> dict[str, Item] | Item | None:
        if exclusion_mode:
            if item:
                return {item.code:item for item in items.values() if item.quantity > 0 and item.code != item}
            elif itemtype or subtype or effect or skill:
                parsed_items: dict[str,Item] = {}
                for code, data in items.items():
                    if itemtype and data.type == itemtype: continue
                    if subtype and data.subtype in subtype: continue
                    if effect and effect in data.effects: continue
                    if skill and skill in data.crafts: continue
                    if data.quantity: parsed_items[code] = data
                return parsed_items
            else:
                return None
        else:
            if item:
                search = items.get(item, None)
                return None if search is None or search.quantity == 0 else search
            elif itemtype or subtype or effect or skill:
                parsed_items: dict[str,Item] = {}
                for code, data in items.items():
                    if itemtype and data.type != itemtype: continue
                    if subtype and not (data.subtype in subtype): continue
                    if effect and not (effect in data.effects): continue
                    if skill and not (skill in data.crafts): continue
                    if data.quantity: parsed_items[code] = data
                return parsed_items
            else:
                return {item.code:item for item in items.values() if item.quantity > 0}