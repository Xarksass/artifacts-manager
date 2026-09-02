from endpoints.endpoint import Endpoint


class MonstersEndpoint(Endpoint):
    endpoint = 'monsters'

    def get_monster_details(self, monster:str):
        path = f'/{monster}'
        return self.fetch(path)
