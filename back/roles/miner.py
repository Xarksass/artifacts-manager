from models.character import Character
from models.locations import Ore
from schemas.item import ResourceType

from roles.gatherer import Gatherer


class Miner(Gatherer):
    className = 'Miner'
    skill = 'mining_level'
    
    def __init__(self, Character: Character) -> None:
        self.resources = {
            'copper': ResourceType(
                code = 'copper_ore',
                required = lambda lvl: lvl > 0,
                gathered = 0,
                threshold = 100,
                location = Ore.COPPER,
            ),
            'iron': ResourceType(
                code = 'iron_ore',
                required = lambda lvl: 9 < lvl,
                gathered = 0,
                threshold = 100,
                location = Ore.IRON,
            ),
            'coal': ResourceType(
                code = 'coal',
                required = lambda lvl: 19 < lvl,
                gathered = 0,
                threshold = 100,
                location = Ore.COAL,
            ),
        }
        super().__init__(Character)