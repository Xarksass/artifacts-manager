from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from dataclass.location import Position


@dataclass
class BaseItem:
    code: str
    quantity: int

@dataclass
class ResourceType:
    code: str
    required: Callable[[int],bool]
    gathered: int
    threshold: int
    location: Position

@dataclass
class Recipe:
    code: str
    name: str
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