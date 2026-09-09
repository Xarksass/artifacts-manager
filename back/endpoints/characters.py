from datetime import UTC, datetime

from core.logger import get_logger
from core.ws_manager import manager
from models.character import Character
from models.cooldown import Cooldown
from models.inventory import Inventory
from schemas.entity import CharacterSchema

from endpoints.endpoint import Endpoint

logger = get_logger(__name__,'characters')

class CharactersEndpoint(Endpoint):
    def __init__(self) -> None:
        self.endpoint = 'my/characters'
        self._cache_namespace = 'character'
        self._cache_expire = 60
        super().__init__()

    async def get_characters(self) -> dict[str,Character]:
        logger.info("Characters list Initialisation ...")
        characters: dict[str,Character] = {}
        response = await self.fetchAll()

        if response:
            for data in response['data']:
                schema: CharacterSchema = CharacterSchema.from_json(data)
                inventory = Inventory([item for item in data['inventory'] if item['code']])

                logger.info(f'{schema.name} Character Initialisation ...')
                character = Character(schema, inventory)

                if datetime.fromisoformat(data['cooldown_expiration']) > datetime.now(UTC):
                    remaining = datetime.fromisoformat(data['cooldown_expiration']) - datetime.now(UTC)
                    character.cooldown = Cooldown(
                        remaining.seconds,
                        data['cooldown_expiration'],
                    )
                    await manager.broadcast({
                        'type': 'cooldown_update',
                        'name': character.name,
                        'data': remaining.seconds
                    })

                characters[character.name] = character
                logger.info(f'Character {character.name} Initialized ...')

        logger.info("Characters list Initialized")
        return characters