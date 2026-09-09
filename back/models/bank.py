import asyncio
from typing import TYPE_CHECKING, Any, Self

from core.logger import get_logger
from endpoints.items import BankEndpoint, ItemsEndpoint
from fastapi_cache import FastAPICache
from schemas.item import Item

from models.grimoire import Grimoire
from models.items import Items

if TYPE_CHECKING:
    from models.character import Character

logger = get_logger(__name__,'bank')

class Bank(Items):
    instance: Self | None = None
    _ready: bool = False

    items: dict[str,int]
    total: int = 0
    api: BankEndpoint
    access_loc: asyncio.Lock

    def __new__(cls) -> Self:
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    @classmethod
    async def create(cls) -> Self:
        """À appeler une seule fois, au démarrage de l'app."""
        self = cls()  # __new__ synchrone, crée ou récupère l'instance
        if not cls._ready:
            logger.info('Bank Initialisation ...')
            cls.instance = super().__new__(cls)
            cls.api = BankEndpoint()
            cls.access_loc = asyncio.Lock()
            cls.items = {}
            logger.info('Bank Syncronisation ...')
            stored_items = await cls.api.get_items()
            if stored_items:
                cls.items = super().parse_items(ItemsEndpoint(), stored_items)
            logger.info('Bank initialized ...')
        return self

    @classmethod
    def open(cls) -> Self:
        """Accès synchrone, à utiliser partout ailleurs une fois `create()` passé."""
        if cls.instance is None or not cls._ready:
            raise RuntimeError("Bank.create() doit être awaité avant tout accès")
        return cls.instance

    # TODO: Check if the bank is full (no slot available), if it happens, chekc gold and try to by expansion

    @classmethod
    async def deposit(cls, character: Character, *, item: Item|None = None, quantity: int|None = None, items: list[dict[str,str|int]]|None = None) -> bool:
        success = False
        while True:
            if not cls.access_loc.locked():
                async with cls.access_loc:
                    if item and quantity:
                        if quantity < 1:
                            raise ValueError
                        
                        await character.log(f"⏳ Store {quantity} {item.name} into the bank...")
                        response = await character.api.store(item.code, quantity)
                        if response:
                            await character.inventory.remove(item.code, quantity)
                            await cls.add(item.code, (quantity * -1))

                            await character.log(f"🏦 Stored {quantity} {item.name} into the bank")
                            if not success: success = True
                    elif items is not None and len(items):
                        await character.log("⏳ Store multiple items into the bank...")
                        response = await character.api.store(items=items)
                        if response:
                            for si in items:
                                stored = await character.inventory.remove(si['code'], si['quantity']) # type: ignore
                                await cls.add(si['code'], si['quantity']) # type: ignore

                                si['name'] = stored.name if isinstance(stored, Item) else si['code']
                            stored_items_str = ", ".join([f"{d['quantity']}x {d['name']}" for d in items])
                            await character.log(f"🏦 {stored_items_str} stored into the bank")
                            if not success: success = True
                
                await FastAPICache.clear(namespace='BANK')
                return success
            else:
                await asyncio.sleep(0.25)

    @classmethod
    async def ask_for_withdraw(cls, character: Character, *, item:str|None = None, quantity: int = 1, itemtype:str|None = None, subtypes:list[str]|None = None, effects:list[str]|None = None, skills:list[str]|None = None) -> bool:
        if quantity < 0:
            raise ValueError
        
        success = False
        while True:
            if not cls.access_loc.locked():
                async with cls.access_loc:
                    if not cls.is_in_bank(item=item, itemtype=itemtype, subtypes=subtypes, effects=effects, skills=skills):
                        return success

                    if item is not None:
                        matched_item = super().get(cls.items, item=item)

                        if matched_item:
                            if quantity > 0:
                                asked_quantity = min(quantity, matched_item)
                            else:
                                asked_quantity = matched_item
                            withdraw_quantity = min(asked_quantity, character.inventory.max_items - character.inventory.total)

                            response = await cls.withdraw(character, item=item, quantity=withdraw_quantity)
                            if response and not success: success = True
                    else:
                        matching_items = super().get(cls.items, itemtype=itemtype, subtypes=subtypes, effects=effects, skills=skills)
                        assert matching_items is not None

                        asked_items: list[dict[str,Any]] = []
                        for code, matched_item in matching_items.items():
                            if quantity > 0:
                                asked_quantity = min(quantity, matched_item)
                            else:
                                asked_quantity = matched_item
                            withdraw_quantity = min(asked_quantity, character.inventory.max_items - character.inventory.total)
                            asked_items.append({"code": code, "quantity": withdraw_quantity})

                        if len(asked_items):
                            response = await cls.withdraw(character, items=asked_items)
                            if response and not success: success = True
                            
                await FastAPICache.clear(namespace='BANK')
                return success
            """ else:
                await asyncio.sleep(0.25) """

    @classmethod
    async def withdraw(cls, character: Character, *, item:str|None = None, quantity: int|None = None, items: list[dict[str,Any]]|None = None) -> dict[str,Any]:
        _grimoire = Grimoire.open()
        if item and quantity:
            item_data = _grimoire.get(item)
            await character.log(f"⏳ withdraw {quantity} {item_data.name} from the bank...")
            response = await character.api.withdraw(item=item_data.code, quantity=quantity)
            if response:
                await character.inventory.add(item_data.code, quantity)
                await cls.remove(item_data.code, quantity)
                await character.log(f"🏦 withdrawn {quantity} {item_data.name} from the bank")
        elif items is not None and len(items):
            logger.debug(f'Trying to withdraw {items!s}')
            await character.log("⏳ withdraw multiple items from the bank...")
            response = await character.api.withdraw(items=items)
            if response:
                for wi in items:
                    withdrawn_data = _grimoire.get(wi['code'])
                    await character.inventory.add(wi['code'], wi['quantity']) # type: ignore
                    await cls.remove(wi['code'], wi['quantity']) # type: ignore
                    wi['name'] = withdrawn_data.name
                w_items_str = ", ".join([f"{d['quantity']}x {d['name']}" for d in items])
                await character.log(f"🏦 {w_items_str} withdrawn from the bank")
        else:
            response = {}
        return response

    @classmethod
    def is_in_bank(cls, *, item:str|None = None, itemtype:str|None = None, subtypes:list[str]|None = None, effects:list[str]|None = None, skills:list[str]|None = None) -> bool:
        _grimoire: Grimoire = Grimoire.open()
        
        if item:
            return bool(cls.items.get(item, None))
        elif itemtype or subtypes or effects or skills:
            for code, quantity in cls.items.items():
                data = _grimoire.get(code)
                if itemtype and data.type != itemtype: continue
                if subtypes and not data.subtype in subtypes: continue
                if effects and not list(set(effects) & set(data.effects.keys())): continue
                if skills and not (set(skills) & set(data.used_in)): continue
                if quantity: return True
            return False
        else:
            return bool(len(cls.items))
   
    @classmethod
    async def add(cls, item:str, quantity:int):
        cls.total += quantity
        return await super().update(ItemsEndpoint(), cls.items, item, quantity, 'BANK')

    @classmethod
    async def remove(cls, item:str, quantity:int):
        cls.total -= quantity
        return await super().update(ItemsEndpoint(), cls.items, item, (quantity * -1), 'BANK')