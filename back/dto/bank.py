from typing import Any

from models.bank import Bank
from pydantic import BaseModel

from dto.item import ItemOut


class BankOut(BaseModel):
    @staticmethod
    def from_bank(b: Bank) -> list[dict[str, Any]]:
        return [ItemOut.from_item(bi).model_dump(mode='json') for bi in b.items.values()]