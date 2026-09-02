#import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from core.logger import get_logger

from .endpoint import Endpoint

if TYPE_CHECKING:
    from commons.character import Character

SKILLS = {
    "mining_level": "mining",
    "woodcutting_level": "woodcutting",
    "fishing_level": "fishing",
    "weaponcrafting_level": "weaponcrafting",
    "gearcrafting_level": "gearcrafting",
    "jewelrycrafting_level": "jewelrycrafting",
    "cooking_level": "cooking",
    "alchemy_level": "alchemy",
}

logger = get_logger(__name__,'character_endpoint')

class CharacterEndpoint(Endpoint):
    loc: tuple[int,int]

    def __init__(self, character: Character) -> None:
        self.character = character
        self.name = character.name
        self.endpoint = f'my/{self.name}/'
        super().__init__()

    async def action(self, action:str, data: dict[str,Any]|list[dict[str,Any]]|None = None) -> dict[str,Any]:
        response = await self.post(action, data)

        logger.debug('check cooldown')
        if self.cooldown is not None and self.cooldown.expiration > datetime.now(UTC):
            self.character.cooldown = self.cooldown

        logger.debug('parse data')
        if 'data' in response:
            dt = response['data']
            ch = None
            if 'character' in dt:
                ch = dt['character']
            elif 'characters' in dt:
                ch = dt['characters'][0]
            if ch is not None:
                if self.character.level != ch['level']: self.character.level = ch['level']
                if self.character.hp != ch['hp']: self.character.hp = ch['hp']
                if self.character.max_hp != ch['max_hp']: self.character.max_hp = ch['max_hp']

                for k, skill in SKILLS.items():
                    logger.debug(f'{skill}: {k} {ch[k]}')
                    if getattr(self.character.skills, skill) != ch[k]: setattr(self.character.skills, skill, ch[k])

            logger.debug('return dt')
            return dt

        logger.debug('return reponse')
        return response

    async def move(self, x:int, y:int) -> dict[str,Any]:
        return await self.action('move', { "x": x, "y": y })

    async def fight(self) -> dict[str,Any]:
        return await self.action('fight')

    async def rest(self) -> dict[str,Any]:
        return await self.action('rest')

    async def use(self, item:str, quantity:int = 1) -> dict[str,Any]:
        return await self.action('use', { "code": item, "quantity": quantity })

    async def craft(self, item:str, quantity:int = 1) -> dict[str,Any]:
        return await self.action('crafting', { "code": item, "quantity": quantity })

    async def gather(self) -> dict[str,Any]:
        return await self.action('gathering')
    
    async def store(self, item:str, quantity: int) -> dict[str,Any]:
        return await self.action('bank/deposit/item', [{"code": item, "quantity": quantity}])

    async def withdraw(self, item:str, quantity: int) -> dict[str,Any]:
        return await self.action('bank/withdraw/item', [{"code": item, "quantity": quantity}])
