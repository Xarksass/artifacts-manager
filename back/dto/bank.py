from typing import Any

from models.bank import Bank
from pydantic import BaseModel

from dto.item import ItemOut


class BankOut(BaseModel):
    @staticmethod
    def from_bank(b: Bank) -> list[dict[str, Any]]:
        return [ItemOut.from_code(c,q).model_dump(mode='json') for c,q in b.items.items()]