from __future__ import annotations

from dataclass.item import Item
from pydantic import BaseModel


class ItemOut(BaseModel):
    name: str
    code: str
    quantity: int
    type: str
    subtype: str
    effects: list[str]
    crafting: list[str]

    @staticmethod
    def from_item(i: Item) -> ItemOut:
        return ItemOut(
            name=i.name,
            code=i.code,
            quantity=i.quantity,
            type=i.type,
            subtype=i.subtype,
            effects=list(i.effects.keys()),
            crafting=list(i.crafts.keys()),
        )