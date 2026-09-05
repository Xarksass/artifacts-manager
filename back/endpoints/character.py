#import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from core.logger import get_logger
from core.ws_manager import manager
from dataclass.character import SKILLS
from fastapi_cache import FastAPICache

from endpoints.endpoint import Endpoint

if TYPE_CHECKING:
    from models.character import Character

logger = get_logger(__name__,'character_endpoint')

class CharacterEndpoint(Endpoint):
    loc: tuple[int,int]

    def __init__(self, character: Character) -> None:
        self.character = character
        self.name = character.name
        self.endpoint = f'my/{self.name}/'
        self._cache_namespace = f'character_{self.name}'
        self._cache_expire = 60
        super().__init__()

    async def action(self, action:str, data: dict[str,Any]|list[dict[str,Any]]|None = None) -> dict[str,Any]:
        response = await self.post(action, data)

        logger.debug('check cooldown')
        if self.cooldown is not None and self.cooldown.expiration > datetime.now(UTC):
            self.character.cooldown = self.cooldown
            await manager.broadcast({
                'type': 'cooldown_update',
                'name': self.name,
                'cd': self.cooldown.remaining
            })

        logger.debug('parse data')
        if 'data' in response:
            await FastAPICache.clear(namespace=self._cache_namespace)
            dt = response['data']
            ch = None
            if 'character' in dt:
                ch = dt['character']
            elif 'characters' in dt:
                ch = dt['characters'][0]
            if ch is not None:
                if self.character.level != ch['level']:
                    await self.character.log(f'Level Up! {self.character.level} -> {ch['level']}')
                    self.character.level = ch['level']
                    self.character.max_hp = ch['max_xp']
                if self.character.hp != ch['xp']: self.character.hp = ch['xp']
                if self.character.hp != ch['hp']: self.character.hp = ch['hp']
                if self.character.max_hp != ch['max_hp']: self.character.max_hp = ch['max_hp']
                if self.character.inventory.max_items != ch['inventory_max_items']: self.character.inventory.max_items = ch['inventory_max_items']

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
        response = await self.action('use', { "code": item, "quantity": quantity })
        if response:
            await self.character.inventory.update(item, (quantity * -1))
        return response

    async def craft(self, item:str, quantity:int = 1) -> dict[str,Any]:
        return await self.action('crafting', { "code": item, "quantity": quantity })

    async def gather(self) -> dict[str,Any]:
        return await self.action('gathering')
    
    async def store(self, item: str|None = None, quantity: int|None = None, items: list[dict[str,str|int]]|None = None) -> dict[str,Any]:
        if item and quantity:
            return await self.action('bank/deposit/item', [{"code": item, "quantity": quantity}])
        elif items is not None and len(items):
            return await self.action('bank/deposit/item', items)
        else:
            return {}

    async def withdraw(self, *,item: str|None = None, quantity: int|None = None, items: list[dict[str,str|int]]|None = None) -> dict[str,Any]:
        if item and quantity:
            return await self.action('bank/withdraw/item', [{"code": item, "quantity": quantity}])
        elif items is not None and len(items):
            return await self.action('bank/withdraw/item', items)
        else:
            return {}
