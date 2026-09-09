from models.character import Character
from models.locations import Fish
from schemas.item import ResourceType

from roles.gatherer import Gatherer


class Fisherman(Gatherer):
    className = 'Fisherman'
    skill = 'fishing_level'
    
    def __init__(self, Character: Character) -> None:
        self.resources = {
            'gudgeon': ResourceType(
                code = 'gudgeon',
                required = lambda lvl: lvl > 0,
                gathered = 0,
                threshold = 100,
                location = Fish.GUDGEON,
            ),
            'shrimp': ResourceType(
                code = 'shrimp',
                required = lambda lvl: 9 < lvl,
                gathered = 0,
                threshold = 100,
                location = Fish.SHRIMP,
            ),
            'bass': ResourceType(
                code = 'bass',
                required = lambda lvl: 19 < lvl,
                gathered = 0,
                threshold = 100,
                location = Fish.BASS,
            ),
            'birctrouth': ResourceType(
                code = 'trout',
                required = lambda lvl: 19 < lvl,
                gathered = 0,
                threshold = 100,
                location = Fish.TROUT,
            ),
        }
        super().__init__(Character)