from typing import Any

from endpoints.endpoint import Endpoint


class ItemsEndpoint(Endpoint):
    endpoint = 'items'
    _cache_namespace = 'items'
    _cache_expire = 6000

    async def get(self, code:str) -> dict[str,Any]:
        return await self.fetch(code)

    async def search(self, craft_material: str, craft_skill: str|None = None) -> list[dict[str,Any]]:
        params = {'craft_material': craft_material}
        if craft_skill:
            params['craft_skill'] = craft_skill
        return await self.fetchAll(params=params)

class BankEndpoint(Endpoint):
    endpoint = 'my/bank'
    _cache_namespace = 'bank'

    async def get_items(self) -> list[dict[str,Any]]:
        return await self.fetchAll('items')