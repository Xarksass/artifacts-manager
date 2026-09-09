from typing import Any

from endpoints.endpoint import Endpoint


class MonstersEndpoint(Endpoint):
    endpoint = 'monsters'
    _cache_namespace = 'monsters'
    _cache_expire = 86400

    async def get_monsters(self, monster:str) -> list[dict[str, Any]]:
        result = await self.fetchAll()
        return [] if not result else result['data']

    async def getAll(self) -> list[dict[str,Any]]:
        result = await self.fetchAll(params={'size': 1})
        if result:
            result = await self.fetchAll(params={'size': result['total']})
        return [] if not result else result['data']

    async def get_monster_details(self, monster:str) -> dict[str, Any]:
        path = f'/{monster}'
        return await self.fetch(path)
