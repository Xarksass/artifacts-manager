from typing import Any

from endpoints.endpoint import Endpoint


class ItemsEndpoint(Endpoint):
    endpoint = 'items'

    def get(self, code:str) -> dict[str,Any]:
        return self.fetch(code)

    def search(self, craft_material: str, craft_skill: str|None = None) -> list[dict[str,Any]]:
        params = {'craft_material': craft_material}
        if craft_skill:
            params['craft_skill'] = craft_skill
        return self.fetchAll(params=params)

class BankEndpoint(Endpoint):
    endpoint = 'my/bank'

    def get_items(self) -> list[dict[str,Any]]:
        return self.fetchAll('items')