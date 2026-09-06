from datetime import UTC, datetime
from enum import Enum, auto
from typing import Any

from core.logger import get_logger
from core.ws_manager import manager
from dataclass.character import SKILLS
from models.character import Character
from models.cooldown import Cooldown

from endpoints.endpoint import Endpoint

logger = get_logger(__name__,'characters')

class Role(Enum):
    HUNTER = auto()
    COOK = auto()

class CharactersEndpoint(Endpoint):
    def __init__(self) -> None:
        self.endpoint = 'my/characters'
        self._cache_namespace = 'character'
        self._cache_expire = 60
        super().__init__()

    async def get_characters(self) -> dict[str,Character]:
        logger.info("Characters' list Initialisation ...")
        characters: dict[str,Character] = {}
        response: list[dict[str,Any]] = await self.fetchAll()

        if response:
            for data in response:
                attributes = {
                    'name': data['name'],
                    'level': data['level'],
                    'hp': data['hp'],
                    'max_hp': data['max_hp'],
                    'xp': data['xp'],
                    'max_xp': data['max_xp'],
                    'gold': data['gold'],
                    'layer': data['layer'],
                    'skin': data['skin'],
                }
                pos = (data['x'],data['y'])
                skills = {v:data[k] for k,v in SKILLS.items()}
                inventory = [item for item in data['inventory'] if item['code']]
                logger.info('Character Initialisation ...')
                ch = await Character.create(attributes, pos, skills, inventory)
                if datetime.fromisoformat(data['cooldown_expiration']) > datetime.now(UTC):
                    remaining = datetime.fromisoformat(data['cooldown_expiration']) - datetime.now(UTC)
                    ch.cooldown = Cooldown(
                        remaining.seconds,
                        data['cooldown_expiration'],
                    )
                    await manager.broadcast({
                        'type': 'cooldown_update',
                        'name': ch.name,
                        'data': remaining.seconds
                    })
                characters[ch.name] = ch
                logger.info('Character Initialized ...')

        logger.info("Characters' list Initialized")
        return characters