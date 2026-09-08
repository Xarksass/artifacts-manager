from endpoints.endpoint import Endpoint


class MonstersEndpoint(Endpoint):
    endpoint = 'monsters'
    _cache_namespace = 'monsters'
    _cache_expire = 86400

    def get_monster_details(self, monster:str):
        path = f'/{monster}'
        return self.fetch(path)
