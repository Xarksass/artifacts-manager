from __future__ import annotations

from models.inventory import Inventory
from pydantic import BaseModel

from dto.item import ItemOut


class InventoryOut(BaseModel):
    total: int
    max: int
    items: list[ItemOut]

    @staticmethod
    def from_inventory(inv: Inventory) -> InventoryOut:
        return InventoryOut(
            total=inv.total,
            max=inv.max_items,
            items=[ItemOut.from_item(i) for i in inv.items.values()]
        )