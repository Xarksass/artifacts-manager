from typing import Any, Self

from core.logger import get_logger
from endpoints.items import ItemsEndpoint
from endpoints.monsters import MonstersEndpoint
from schemas.entity import MonsterSchema
from schemas.item import Item, Recipe

logger = get_logger(__name__,'grimoire')

class Grimoire:
    instance: Self | None = None
    _ready: bool = False

    items: dict[str, Item]
    recipes: dict[str, list[Recipe]]
    monsters: dict[str, MonsterSchema]
    locations: dict[str, Any]
    items_api: ItemsEndpoint
    monsters_api: MonstersEndpoint

    def __new__(cls) -> Self:
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    @classmethod
    async def create(cls) -> Self:
        """À appeler une seule fois, au démarrage de l'app."""
        self = cls()  # __new__ synchrone, crée ou récupère l'instance
        if not cls._ready:
            cls.items_api = ItemsEndpoint()
            cls.items = {}
            cls.recipes = {}
            items_data = await cls.items_api.getAll()
            logger.debug(f'len(items_data) = {len(items_data)}')
            if items_data:
                cls.parse_items(items_data)

            cls.monsters_api = MonstersEndpoint()
            cls.monsters = {}
            monsters_data = await cls.monsters_api.getAll()
            if monsters_data:
                cls.parse_monsters(monsters_data)

            cls._ready = True
        return self

    @classmethod
    def get(cls) -> Self:
        """Accès synchrone, à utiliser partout ailleurs une fois `create()` passé."""
        if cls.instance is None or not cls._ready:
            raise RuntimeError("Grimoire.create() doit être awaité avant tout accès")
        return cls.instance

    @classmethod
    def parse_items(cls, items: list[dict[str,Any]]) -> None:
        parsed_items: dict[str,Item] = {}
        for item in items:
            recipe = None
            if item['craft']:
                craft:dict[str,Any] = item['craft']
                recipe = Recipe(
                    item['code'],
                    item['name'],
                    craft['skill'],
                    craft['level'],
                    {bi['code']:bi['quantity'] for bi in craft['items']},
                    craft['quantity']
                )
                recipe_list = cls.recipes.setdefault(craft['skill'],[])
                recipe_list.append(recipe)
            
            parsed_items[item['code']] = Item(
                item['name'], 
                item['code'], 
                item['level'], 
                item['type'], 
                item['subtype'], 
                item['conditions'], 
                {effect['code']:effect['value'] for effect in item['effects']}, 
                set(), 
                item['tradeable'], 
                item['recyclable'],
                recipe,
            )
        cls.items = parsed_items

        for skill, recipe_list in cls.recipes.items():
            recipe_list.sort(key = lambda r: (r.level * -1))

            parsed = {}
            for recipe in recipe_list:
                for craft_item in recipe.items:
                    if craft_item not in parsed:
                        cls.items[craft_item].used_in.add(skill)

    @classmethod
    def parse_monsters(cls, monsters: list[dict[str,Any]]) -> None:
        parsed_data: dict[str,MonsterSchema] = {}
        for monster in monsters:
            parsed_data[monster['code']] = MonsterSchema.from_json(monster)
        cls.monsters = parsed_data