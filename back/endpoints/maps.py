from endpoints.endpoint import Endpoint


class MapsEndpoint(Endpoint):
    endpoint = 'maps'

    def __init__(self, layer:str = 'overworld') -> None:
        super().__init__()
        self.layer = layer

    async def get_cell_details(self, x:int, y:int):
        path = f'{self.layer}/{x}/{y}'
        return await self.fetch(path)
