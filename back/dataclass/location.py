from dataclasses import dataclass


@dataclass
class Position:
    x: int
    y: int

@dataclass
class MapContent:
    type: str
    code: str

@dataclass
class MapTansition:
    map_id: int
    pos: Position

@dataclass
class MapInteractions:
    content: MapContent
    transition: MapTansition

@dataclass
class Map:
    id: int
    name: str
    pos: Position
    skin: str
    layer: str