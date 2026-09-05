from endpoints.endpoint import Endpoint


class MapsEndpoint(Endpoint):
    endpoint = 'maps'
    _cache_namespace = 'maps'
    _cache_expire = 6000

    def __init__(self, layer:str = 'overworld') -> None:
        super().__init__()
        self.layer = layer

    async def get_cell_details(self, x:int, y:int):
        path = f'{self.layer}/{x}/{y}'
        return await self.fetch(path)
