from dataclass.item import ResourceType
from models.character import Character
from models.locations import Plant

from roles.gatherer import Gatherer


class Picker(Gatherer):
    className = 'Picker'
    
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