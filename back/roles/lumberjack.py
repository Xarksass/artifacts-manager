from dataclass.item import ResourceType
from models.character import Character
from models.locations import Wood

from roles.gatherer import Gatherer


class Lumberjack(Gatherer):
    className = 'Lumberjack'
    
    def __init__(self, Character: Character) -> None:
        self.resources = {
            'ash': ResourceType(
                code = 'ash_wood',
                required = lambda lvl: lvl > 0,
                gathered = 0,
                threshold = 100,
                location = Wood.ASH,
            ),
            'spruce': ResourceType(
                code = 'spruce_wood',
                required = lambda lvl: 9 < lvl,
                gathered = 0,
                threshold = 100,
                location = Wood.SPRUCE,
            ),
            'birch': ResourceType(
                code = 'birch_wood',
                required = lambda lvl: 19 < lvl,
                gathered = 0,
                threshold = 100,
                location = Wood.BIRCH,
            ),
            'mapple': ResourceType(
                code = 'mapple_wood',
                required = lambda lvl: 39 < lvl,
                gathered = 0,
                threshold = 100,
                location = Wood.MAPPLE,
            ),
        }
        super().__init__(Character)