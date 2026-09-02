import asyncio
from typing import TYPE_CHECKING, Any, Self

from commons.items import Items
from core.logger import get_logger
from dataclass.item import Item
from endpoints.items import BankEndpoint, ItemsEndpoint

if TYPE_CHECKING:
    from commons.character import Character

logger = get_logger(__name__,'bank')

class Bank(Items):
    instance: Self|None = None
    items: dict[str,Item]
    api: BankEndpoint
    access_loc: asyncio.Lock

    def __new__(cls) -> Self:
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            cls.api = BankEndpoint()
            cls.access_loc = asyncio.Lock()
            cls.items = {}

            stored_items = cls.api.get_items()
            if stored_items:
                cls.items = super().parse_items(ItemsEndpoint(), stored_items)

        return cls.instance

    # TODO: Check if the bank is full (no slot available), if it happens, chekc gold and try to by expansion

    @classmethod
    async def deposit(cls, character: Character, item: Item, quantity: int = 1) -> bool:
        if quantity < 1:
            raise ValueError
        
        success = False
        while True:
            if not cls.access_loc.locked():
                async with cls.access_loc:
                    character.window.log(f"Store {quantity} {item.name} into the bank...")
                    response = await character.api.store(item.code, quantity)
                    if response:
                        character.inventory.update(item.code, (quantity * -1))
                        character.window.log(f"Stored {quantity} {item.name} into the bank")
                        if response and not success: success = True
                
                return success
            else:
                await asyncio.sleep(0.25)

    @classmethod
    async def ask_for_withdraw(cls, character: Character, *, item:str|None = None, quantity: int = 1, itemtype:str|None = None, subtype:list[str]|None = None, effect:str|None = None, skill:str|None = None) -> bool:
        if quantity < 0:
            raise ValueError
        
        success = False
        while True:
            if not cls.access_loc.locked():
                async with cls.access_loc:
                    if not cls.is_in_bank(item=item, itemtype=itemtype, subtype=subtype, effect=effect, skill=skill):
                        return success

                    if item is not None:
                        matched_item = super().get(cls.items, item=item)

                        assert matched_item is not None
                        withdraw_quantity = min(quantity, matched_item.quantity) if quantity > 0 else matched_item.quantity
                        response = await cls.withdraw(character, matched_item, withdraw_quantity)
                        if response and not success: success = True
                    else:
                        matching_items = super().get(cls.items, itemtype=itemtype, subtype=subtype, effect=effect, skill=skill)

                        assert matching_items is not None
                        for matched_item in matching_items.values():
                            withdraw_quantity = min(quantity, matched_item.quantity) if quantity > 0 else matched_item.quantity
                            response = await cls.withdraw(character, matched_item, withdraw_quantity)
                            if response and not success: success = True
                return success
            else:
                await asyncio.sleep(0.25)


    @classmethod
    async def withdraw(cls, character: Character, item:Item, quantity: int) -> dict[str,Any]:
        character.window.log(f"withdraw {quantity} {item.name} from the bank...")

        response = await character.api.withdraw(item.code, quantity)
        if response:
            character.inventory.update(item.code, quantity)
            character.window.log(f"withdrawn {quantity} {item.name} from the bank")
        return response

    @classmethod
    def is_in_bank(cls, *, item:str|None = None, itemtype:str|None = None, subtype:list[str]|None = None, effect:str|None = None, skill:str|None = None) -> bool:
        if item:
            return bool(cls.items.get(item, None))
        elif itemtype or subtype or effect or skill:
            for data in cls.items.values():
                if itemtype and data.type != itemtype: continue
                if subtype and not data.subtype in subtype: continue
                if effect and not effect in data.effects: continue
                if data.quantity: return True
            return False
        else:
            return bool(len(cls.items))