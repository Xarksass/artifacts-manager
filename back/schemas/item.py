from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from schemas.location import Position


@dataclass
class Effect:
    code: str
    value: int

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
    used_in: set[str]
    tradeable: bool
    recyclable: bool
    recipe: Recipe|None = None