from datetime import UTC, datetime
from enum import Enum, auto
from typing import Any

from commons.character import SKILLS, Character
from core.logger import get_logger
from endpoints.endpoint import Cooldown

from .endpoint import Endpoint

logger = get_logger(__name__,'characters')

class Role(Enum):
    HUNTER = auto()
    COOK = auto()

class CharactersEndpoint(Endpoint):
    def __init__(self) -> None:
        self.endpoint = 'my/characters'
        super().__init__()

    async def get_characters(self) -> list[Character]:
        characters: list[Character] = []
        response: list[dict[str,Any]] = self.fetchAll()

        if response:
            for data in response:
                hp = (data['hp'],data['max_hp'])
                pos = (data['x'],data['y'])
                skills = {v:data[k] for k,v in SKILLS.items()}
                inventory = [item for item in data['inventory'] if item['code']]
                ch = Character(data['name'], data['level'], hp, pos, skills, inventory)
                if datetime.fromisoformat(data['cooldown_expiration']) > datetime.now(UTC):
                    remaining = datetime.fromisoformat(data['cooldown_expiration']) - datetime.now(UTC)
                    ch.cooldown = Cooldown(
                        remaining.seconds,
                        data['cooldown_expiration'],
                    )
                characters.append(ch)

        return characters