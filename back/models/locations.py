from dataclass.location import Position


class Location:
    SPAWN = Position(0,0)
    BANK = Position(4,1)
    GE = Position(5,1)

class Workshop:
    COOKING = Position(1,1)
    WEAPON = Position(2,1)
    GEAR = Position(3,1)
    JEWELRY = Position(1,3)
    ALCHEMY = Position(2,3)

class NPC:
    TASK = Position(1,2)
    TAILOR = Position(3,3)

class Resource:
    ASH = Position(-1,0)
    SUNFLOWER = Position(2,2)
    COPPER = Position(2,0)

class FishLocation:
    GUDGEON = Position(4,2)
    SHRIMP = Position(5,2)
    BASS = Position(6,12)
    TROUT = Position(7,12)

class Monster:
    CHICKEN = Position(0,1)
    YELLOW_SLIME = Position(1,-2)
    GREEN_SLIME = Position(0,-1)
    BLUE_SLIME = Position(0,-2)
    RED_SLIME = Position(1,-1)
    COW = Position(0,2)
    MUSHMUSH = Position(5,3)
    FLYING_SNAKE = Position(5,4)
    WOLF = Position(-2,1)
    PIG = Position(-3,-3)
