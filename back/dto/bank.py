from models.bank import Bank
from pydantic import BaseModel

from dto.item import ItemOut


class BankOut(BaseModel):
    @staticmethod
    def from_bank(b: Bank) -> list[ItemOut]:
        return [ItemOut.from_item(bi) for bi in b.items.values()]