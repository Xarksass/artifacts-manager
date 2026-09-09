from __future__ import annotations

from models.grimoire import Grimoire
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
    def from_code(code: str, quantity: int) -> ItemOut:
        _grimoire = Grimoire.open()
        item_data = _grimoire.get(code)
        return ItemOut(
            name=item_data.name,
            code=item_data.code,
            quantity=quantity,
            type=item_data.type,
            subtype=item_data.subtype,
            effects=list(item_data.effects.keys()),
            crafting=list(item_data.used_in),
        )