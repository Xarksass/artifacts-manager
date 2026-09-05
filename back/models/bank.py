import asyncio
from typing import TYPE_CHECKING, Any, Self

from core.logger import get_logger
from dataclass.item import Item
from endpoints.items import BankEndpoint, ItemsEndpoint

from models.items import Items

if TYPE_CHECKING:
    from models.character import Character

logger = get_logger(__name__,'bank')

class Bank(Items):
    instance: Self|None = None
    items: dict[str,Item]
    api: BankEndpoint
    access_loc: asyncio.Lock

    async def __new__(cls) -> Self:
        if cls.instance is None:
            logger.info('Bank Initialisation ...')
            cls.instance = super().__new__(cls)
            cls.api = BankEndpoint()
            cls.access_loc = asyncio.Lock()
            cls.items = {}
            logger.info('Bank Syncronisation ...')
            stored_items = await cls.api.get_items()
            if stored_items:
                cls.items = await super().parse_items(ItemsEndpoint(), stored_items)
            logger.info('Bank initialized ...')
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
                        
                        #character.window.log(f"⏳ Store {quantity} {item.name} into the bank...")
                        response = await character.api.store(item.code, quantity)
                        if response:
                            await character.inventory.update(item.code, (quantity * -1))
                            #character.window.log(f"🏦 Stored {quantity} {item.name} into the bank")
                            if not success: success = True
                    elif items is not None and len(items):
                        #character.window.log("⏳ Store multiple items into the bank...")
                        response = await character.api.store(items=items)
                        if response:
                            for si in items:
                                stored = await character.inventory.update(si['code'], (si['quantity'] * -1)) # type: ignore
                                si['name'] = stored.name if isinstance(stored, Item) else si['code']
                            #stored_items_str = ", ".join([f"{d['quantity']}x {d['name']}" for d in items])
                            #character.window.log(f"🏦 {stored_items_str} stored into the bank")
                            if not success: success = True
                
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
                        assert matched_item is not None

                        if quantity > 0:
                            asked_quantity = min(quantity, matched_item.quantity)
                        else:
                            asked_quantity = matched_item.quantity
                        withdraw_quantity = min(asked_quantity, character.inventory.max_items - character.inventory.total)

                        response = await cls.withdraw(character, item=matched_item, quantity=withdraw_quantity)
                        if response and not success: success = True
                    else:
                        matching_items = super().get(cls.items, itemtype=itemtype, subtypes=subtypes, effects=effects, skills=skills)
                        assert matching_items is not None

                        asked_items: list[dict[str,str|int]] = []
                        for matched_item in matching_items.values():
                            if quantity > 0:
                                asked_quantity = min(quantity, matched_item.quantity)
                            else:
                                asked_quantity = matched_item.quantity
                            withdraw_quantity = min(asked_quantity, character.inventory.max_items - character.inventory.total)
                            asked_items.append({"code": matched_item.code, "quantity": withdraw_quantity})

                        if len(asked_items):
                            response = await cls.withdraw(character, items=asked_items)
                            if response and not success: success = True
                return success
            """ else:
                await asyncio.sleep(0.25) """


    @classmethod
    async def withdraw(cls, character: Character, *, item:Item|None = None, quantity: int|None = None, items: list[dict[str,str|int]]|None = None) -> dict[str,Any]:
        if item and quantity:
            #character.window.log(f"⏳ withdraw {quantity} {item.name} from the bank...")
            response = await character.api.withdraw(item=item.code, quantity=quantity)
            if response:
                await character.inventory.update(item.code, quantity)
                #character.window.log(f"🏦 withdrawn {quantity} {item.name} from the bank")
        elif items is not None and len(items):
            #character.window.log("⏳ withdraw multiple items from the bank...")
            response = await character.api.withdraw(items=items)
            if response:
                for wi in items:
                    withdrawn = await character.inventory.update(wi['code'], wi['quantity']) # type: ignore
                    wi['name'] = withdrawn.name if isinstance(withdrawn, Item) else wi['code']
                #w_items_str = ", ".join([f"{d['quantity']}x {d['name']}" for d in items])
                #character.window.log(f"🏦 {w_items_str} withdrawn from the bank")
        else:
            response = {}
        return response

    @classmethod
    def is_in_bank(cls, *, item:str|None = None, itemtype:str|None = None, subtypes:list[str]|None = None, effects:list[str]|None = None, skills:list[str]|None = None) -> bool:
        if item:
            return bool(cls.items.get(item, None))
        elif itemtype or subtypes or effects or skills:
            for data in cls.items.values():
                if itemtype and data.type != itemtype: continue
                if subtypes and not data.subtype in subtypes: continue
                if effects and not list(set(effects) & set(data.effects.keys())): continue
                if skills and not list(set(skills) & set(data.crafts.keys())): continue
                if data.quantity: return True
            return False
        else:
            return bool(len(cls.items))