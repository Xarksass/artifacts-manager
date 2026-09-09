from models.character import Character
from models.locations import Plant
from schemas.item import ResourceType

from roles.gatherer import Gatherer


class Picker(Gatherer):
    className = 'Picker'
    skill = 'alchemy_level'
    
    def __init__(self, Character: Character) -> None:
        self.resources = {
            'sunflower': ResourceType(
                code = 'sunflower',
                required = lambda lvl: lvl > 0,
                gathered = 0,
                threshold = 100,
                location = Plant.SUNFLOWER,
            ),
            'nettle': ResourceType(
                code = 'nettle_leaf',
                required = lambda lvl: 19 < lvl,
                gathered = 0,
                threshold = 100,
                location = Plant.NETTLE,
            ),
            'glowstem': ResourceType(
                code = 'glowstem_leaf',
                required = lambda lvl: 39 < lvl,
                gathered = 0,
                threshold = 100,
                location = Plant.GLOWSTEM,
            ),
        }
        super().__init__(Character)