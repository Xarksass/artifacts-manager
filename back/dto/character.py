from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from models.character import Character

class CharacterOut(BaseModel):
    name: str
    level: int
    hp: int
    max_hp: int
    xp: int
    max_xp: int
    x: int
    y: int
    skin: str
    cooldown_expiration: datetime | None

    @staticmethod
    def from_character(c: Character) -> CharacterOut:
        return CharacterOut(
            name=c.name, 
            level=c.level,
            hp=c.hp, 
            max_hp=c.max_hp,
            xp=c.xp,
            max_xp=c.max_xp,
            x=c.pos.x,
            y=c.pos.y,
            skin=c.skin,
            cooldown_expiration=c.cooldown.expiration if c.cooldown else None,
        )