from dataclasses import dataclass
from typing import Any


@dataclass
class BaseItem:
    code: str
    quantity: int

@dataclass
class Recipe:
    code: str
    skill: str
    level: str
    items: dict[str,int]
    quantity: int

@dataclass
class Item:
    name: str
    code: str
    level: int
    type: str
    subtype: str
    conditions: list[dict[str,Any]]
    effects: dict[str,Any]
    crafts: dict[str,list[Recipe]]
    tradeable: bool
    recyclable: bool
    quantity: int