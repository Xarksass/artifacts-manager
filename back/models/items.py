from abc import ABC
from typing import Any, overload

from core.logger import get_logger
from dataclass.item import Item, Recipe
from endpoints.items import ItemsEndpoint
from fastapi_cache import FastAPICache

logger = get_logger(__name__,'items')

class Items(ABC):
    items: dict[str,Item]

    @staticmethod
    async def get_recipes(api: ItemsEndpoint, item: str) -> dict[str,list[Recipe]]:
        craft_list = await api.search(item)
        crafts: dict[str,list[Recipe]] = {}

        for craftable in craft_list:
            craft = craftable['craft']
            recipe_list = crafts.setdefault(craft['skill'],[])
            recipe_list.append(Recipe(
                craftable['code'],
                craftable['name'],
                craft['skill'],
                craft['level'],
                {bi['code']:bi['quantity'] for bi in craft['items']},
                craft['quantity']
            ))

        for key, recipe_list in crafts.items():
            crafts[key] = sorted(recipe_list, key=lambda x: (x.level *-1))

        return crafts

    @staticmethod
    async def parse_items(api: ItemsEndpoint, items: list[dict[str,Any]]) -> dict[str,Item]:
        parsed_items: dict[str,Item] = {}
        for item in items:
            item_data = await api.fetch(item['code'])
            if item_data:
                crafts = await Items.get_recipes(api, item_data['code'])
                
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
    def get(items:dict[str,Item], *, item: str, itemtype: None = None, subtypes: None = None, effects: None = None, skills: None = None, exclusion_mode: bool = False) -> Item | None: ...
    @overload
    @staticmethod
    def get(items:dict[str,Item], *, item: None = None, itemtype: str | None = None, subtypes: list[str] | None = None, effects: list[str] | None = None, skills: list[str] | None = None, exclusion_mode: bool = False) -> dict[str, Item] | None: ...
    @staticmethod
    def get(items:dict[str,Item], *, 
            item: str | None = None, 
            itemtype: str | None = None, 
            subtypes: list[str] | None = None, 
            effects: list[str] | None = None, 
            skills: list[str] | None = None,
            exclusion_mode: bool = False) -> dict[str, Item] | Item | None:
        if exclusion_mode:
            if item:
                return {item.code:item for item in items.values() if item.quantity > 0 and item.code != item}
            elif itemtype or subtypes or effects or skills:
                parsed_items: dict[str,Item] = {}
                for code, data in items.items():
                    if itemtype and data.type != itemtype: continue
                    if subtypes and not data.subtype in subtypes: continue
                    if effects and list(set(effects) & set(data.effects.keys())): continue
                    if skills and list(set(skills) & set(data.crafts.keys())): continue
                    if data.quantity: parsed_items[code] = data
                return parsed_items
            else:
                return None
        else:
            if item:
                search = items.get(item, None)
                return None if search is None or search.quantity == 0 else search
            elif itemtype or subtypes or effects or skills:
                parsed_items: dict[str,Item] = {}
                for code, data in items.items():
                    if itemtype and data.type != itemtype: continue
                    if subtypes and not data.subtype in subtypes: continue
                    if effects and not list(set(effects) & set(data.effects.keys())): continue
                    if skills and not list(set(skills) & set(data.crafts.keys())): continue
                    if data.quantity: parsed_items[code] = data
                return parsed_items
            else:
                return {item.code:item for item in items.values() if item.quantity > 0}

    @staticmethod
    async def update(api: ItemsEndpoint, items: dict[str, Item], item:str, quantity:int, namespace: str) -> Item|None:
        stored = items.get(item)

        if stored is None:
            if quantity < 0:
                return
            
            item_data = await api.get(item)
            if item_data:
                crafts = await Items.get_recipes(api, item_data['code'])

                stored = Item(
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
                    quantity
                )
                items[item_data['code']] = stored
        else:
            stored.quantity += quantity

        await FastAPICache.clear(namespace=namespace)
        return stored