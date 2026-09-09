from typing import Any

from endpoints.endpoint import Endpoint


class ItemsEndpoint(Endpoint):
    endpoint = 'items'
    _cache_namespace = 'items'
    _cache_expire = 86400
    
    async def get(self, code:str) -> dict[str,Any]:
        return await self.fetch(code)

    async def getAll(self) -> list[dict[str,Any]]:
        # get total available data
        result = await self.fetchAll(params={'size': 1})
        if result:
            # retrieve total available data
            result = await self.fetchAll(params={'size': result['total']})
        return [] if not result else result['data']

    async def search(self, craft_material: str, craft_skill: str|None = None) -> list[dict[str,Any]]:
        params = {'craft_material': craft_material}
        if craft_skill:
            params['craft_skill'] = craft_skill
        result = await self.fetchAll(params=params)
        return [] if not result else result['data']

class BankEndpoint(Endpoint):
    endpoint = 'my/bank'
    _cache_namespace = 'bank'

    async def get_items(self) -> list[dict[str,Any]]:
        result =  await self.fetchAll('items')
        return [] if not result else result['data']