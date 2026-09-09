from abc import ABC
from typing import Any, overload

from endpoints.items import ItemsEndpoint
from fastapi_cache import FastAPICache
from schemas.item import Recipe

from models.grimoire import Grimoire


class Items(ABC):
    items: dict[str,int]

    @staticmethod
    async def get_recipes(api: ItemsEndpoint, item: str) -> dict[str,list[Recipe]]:
        """ Deprecated. ToDo: replace using the grimoire """
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
    def parse_items(api: ItemsEndpoint, items: list[dict[str,Any]]) -> dict[str,int]:
        #grimoire = Grimoire.get()
        parsed_items: dict[str,int] = {}
        for item in items:
            #item_data = grimoire.items.get(item['code'])
            #if item_data:
                #parsed_items[item['code']] = deepcopy(item_data)
            parsed_items[item['code']] = item['quantity']
        return parsed_items
    
    @overload
    @staticmethod
    def get(items:dict[str,int], *, item: str, itemtype: None = None, subtypes: None = None, effects: None = None, skills: None = None, exclusion_mode: bool = False) -> int | None: ...
    @overload
    @staticmethod
    def get(items:dict[str,int], *, item: None = None, itemtype: str | None = None, subtypes: list[str] | None = None, effects: list[str] | None = None, skills: list[str] | None = None, exclusion_mode: bool = False) -> dict[str, int] | None: ...
    @staticmethod
    def get(items:dict[str,int], *, 
            item: str | None = None, 
            itemtype: str | None = None, 
            subtypes: list[str] | None = None, 
            effects: list[str] | None = None, 
            skills: list[str] | None = None,
            exclusion_mode: bool = False) -> dict[str, int] | int | None:

        _grimoire: Grimoire = Grimoire.open()
        if exclusion_mode:
            if item:
                return {code:quantity for code, quantity in items.items() if quantity and code != item}
            elif itemtype or subtypes or effects or skills:
                parsed_items: dict[str,int] = {}
                for code, quantity in items.items():
                    data = _grimoire.get(code)
                    if itemtype and data.type != itemtype: continue
                    if subtypes and not data.subtype in subtypes: continue
                    if effects and list(set(effects) & set(data.effects.keys())): continue
                    if skills and (set(skills) & set(data.used_in)): continue
                    if quantity: parsed_items[code] = quantity
                return parsed_items
            else:
                return None
        else:
            if item:
                search = items.get(item, None)
                return None if not search else items.get(item)
            elif itemtype or subtypes or effects or skills:
                parsed_items: dict[str,int] = {}
                for code, quantity in items.items():
                    data = _grimoire.get(code)
                    if itemtype and data.type != itemtype: continue
                    if subtypes and not data.subtype in subtypes: continue
                    if effects and not list(set(effects) & set(data.effects.keys())): continue
                    if skills and not (set(skills) & data.used_in): continue
                    if quantity: parsed_items[code] = quantity
                return parsed_items
            else:
                return {code:quantity for code, quantity in items.items() if quantity}

    @staticmethod
    async def update(api: ItemsEndpoint, items: dict[str, int], item:str, quantity:int, namespace: str) -> int|None:
        stored = items.get(item)

        if stored is None:
            if quantity < 0:
                return
            
            items[item] = quantity
        else:
            items[item] += quantity

        await FastAPICache.clear(namespace=namespace)
        return items[item]