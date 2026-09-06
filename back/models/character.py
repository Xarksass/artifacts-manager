import asyncio
from collections import deque
from collections.abc import Callable
from typing import Any, Self

from core.ws_manager import manager
from dataclass.character import Skills
from dataclass.item import Item, Recipe
from endpoints.character import CharacterEndpoint
from endpoints.endpoint import Cooldown
from endpoints.maps import MapsEndpoint

#from cli.window.character import CharacterWindow
from endpoints.monsters import MonstersEndpoint

#from endpoints.monsters import MonstersEndpoint
from roles.role import Role

from models.inventory import Inventory
from models.locations import Position


class Character:
    name: str
    level: int
    gold: int
    hp: int
    max_hp: int
    xp: int
    max_xp: int
    layer: str
    skin: str
    pos: Position
    inventory: Inventory
    skills: Skills
    role: Role
    api: CharacterEndpoint
    _next_ready_at: float | None # deadline absolue (loop.time())
    __cooldown: Cooldown | None = None
    __logs: deque[str]
    #__window: CharacterWindow

    @classmethod
    async def create(cls, attributes:dict[str,Any], pos:tuple[int,int], skills: dict[str,int], inventory: list[dict[str,Any]]) -> Self:
        self = cls()
        for attribute, value in attributes.items():
            setattr(self, attribute, value)
        self.pos = Position(*pos)
        self.inventory = await Inventory.create(inventory)
        self.skills = Skills(**skills)
        self.api = CharacterEndpoint(self)
        self.role = Role(self)
        self._next_ready_at = None
        self.__logs = deque([])
        return self

    """ @property
    def window(self) -> CharacterWindow:
        return self.__window

    @window.setter
    def window(self, window: CharacterWindow) -> None:
        self.__window = window
        self.window.action = 'idle' """
    
    @property
    def logs(self) -> deque[str]:
        return self.__logs

    @property
    def cooldown(self) -> Cooldown|None: return self.__cooldown

    @cooldown.setter
    def cooldown(self, cd: Cooldown) -> None:
        self.__cooldown = cd
        self._next_ready_at = asyncio.get_running_loop().time() + cd.remaining
        #if cd.remaining:
        #    asyncio.create_task(self.window.run_cooldown(asyncio.Event()))

    # Methods
    async def log(self, entry: str) -> None:
        self.__logs.append(entry)
        await manager.broadcast({
            'type': 'log_update',
            'name': self.name,
            'data': list(self.__logs)
        })

    def next_ready_at(self) -> float | None:
        """Renvoie la deadline absolue du prochain tick possible, ou None si prêt maintenant."""
        return self._next_ready_at

    def is_item_usable(self, item_data: Item) -> bool:
        passed = True
        comp: dict[str,Callable[[int,int],bool]] = {
            'eq': lambda c,v: c == v,
            'ne': lambda c,v: c != v,
            'gt': lambda c,v: c > v,
            'lt': lambda c,v: c < v,
        }
        for cond in item_data.conditions:
            if  not comp[cond['operator']](getattr(self, cond['code']), cond['value']):
                passed = False
                break;
        return passed

    def select_best_heal_item(self, items: dict[str,Item]) -> tuple[Item|None,int]:
        min_diff = self.max_hp - self.hp
        to_heal = self.max_hp - self.hp
        to_use = None

        for item in items.values():
            if not self.is_item_usable(item): continue;
            diff = to_heal - item.effects['heal']
            if abs(diff) < min_diff:
                min_diff = diff
                to_use = item
        return to_use, max(0, min_diff)

    def craftable(self, skill:str, recipe: Recipe) -> int:
        if recipe.level > getattr(self.skills,skill):
            return 0
        
        count = None
        for code, quantity in recipe.items.items():
            in_bag = self.inventory.pick(item=code)
            if not in_bag or in_bag.quantity < quantity:
                return 0
            available = in_bag.quantity // quantity
            count = available if count is None else min(count, available)

        assert count is not None
        return count

    # ACtions
    async def move(self, mx:int, my:int) -> None:
        await self.move_to(self.pos.x + mx,self.pos.y + my)

    async def move_to(self, x:int, y:int) -> None:
        map_api = MapsEndpoint()
        from_details = await map_api.get_cell_details(self.pos.x, self.pos.y)
        to_details = await map_api.get_cell_details(x, y)

        from_name = f'{from_details['name']}'
        if 'interactions' in from_details and 'content' in from_details['interactions'] and bool(from_details['interactions']['content']):
                from_iter = from_details['interactions']['content']
                from_name += f' - {from_iter['code'].replace('_','').capitalize()}({from_iter['type'].replace('_','').capitalize()})'

        to_name = f'{to_details['name']}'
        if 'interactions' in to_details and 'content' in to_details['interactions'] and bool(to_details['interactions']['content']):
                to_iter = to_details['interactions']['content']
                to_name += f' - {to_iter['code'].replace('_','').capitalize()}({to_iter['type'].replace('_','').capitalize()})'

        await self.log(f'⏳ Moving from {from_name} to {to_name}...')
        response = await self.api.move(x,y)
        if response:
            await self.log(f'👢 Moved from {from_name} to {to_name} on {response["destination"]['name']}.')
            self.pos = Position(x,y)

    async def fight(self) -> None:
        map_api = MapsEndpoint()
        map_details = await map_api.get_cell_details(self.pos.x, self.pos.y)
        if 'interactions' in map_details:
            iter_type = map_details['interactions']['content']
            if iter_type['type'] == 'monster':
                monster_api = MonstersEndpoint()
                monster = await monster_api.get_monster_details(iter_type['code'])
            
                await self.log(f'⚔️ Attacking {monster['name']}...')
                response = await self.api.fight()

                if response:
                    fight = response["fight"]
                    fight_stats = fight["characters"][0]
                    
                    await self.log("🏆 Fight won!" if fight["result"] == "win" else "💀 Fight lost!")
                    await self.log(f"⚔️  XP gained: {fight_stats['xp']} | HP remaining: {fight_stats['final_hp']}")
                    
                    if len(fight_stats["drops"]) > 0:
                        for d in fight_stats['drops']:
                            drop = await self.inventory.update(d['code'], d['quantity'])
                            d['name'] = drop.name if isinstance(drop, Item) else d['code']
                        drops_str = ", ".join([f"{d['quantity']}x {d['name']}" for d in fight_stats["drops"]])
                        await self.log(f"🎁 Loot dropped: {drops_str}")

    async def rest(self) -> int:
        #self.window.log('🛌 Resting...')
        response = await self.api.rest()
        return response["hp_restored"]
    
    async def eat(self) -> int:
        cooked_food = self.inventory.pick(itemtype='consumable',subtypes=['food'], effects=['heal'])

        if cooked_food:
            to_eat, diff = self.select_best_heal_item(cooked_food)
            hp_restored = self.max_hp - self.hp - diff
            
            if to_eat is not None:
                #self.window.log(f'⏳ Eating a portion of {to_eat.name}...')
                await self.api.use(to_eat.code)
                #self.window.log(f'🍴 1 portion of {to_eat.name} eaten.')
                return hp_restored
        return 0

    async def drink(self) -> int:
        potions = self.inventory.pick(itemtype='consumable',subtypes=['potion'], effects=['heal'])

        if potions:
            to_drink, diff = self.select_best_heal_item(potions)
            hp_restored = self.max_hp - self.hp - diff
            
            if to_drink is not None:
                #self.window.log(f'⏳ Drinking {to_drink.name}...')
                await self.api.use(to_drink.code)
                #self.window.log(f'🍵 1 {to_drink.name} drank.')
                return hp_restored
        return 0

    async def heal(self) -> None:
        hp_restored = 0

        if self.inventory.pick(itemtype='consumable',subtypes=['potion']):
            hp_restored = await self.drink()

        if not hp_restored and self.inventory.pick(itemtype='consumable',subtypes=['food']):
            hp_restored = await self.eat()

        if not hp_restored:
            hp_restored = await self.rest()

        #self.window.log(f"Restored {hp_restored} HP.")
        #self.window.log(f"❤️ Current HP: {self.hp}/{self.max_hp}")

    async def craft(self, recipe:Recipe, quantity:int = 1) -> dict[str,Any]:
        #self.window.log(f'⏳ Crafting {quantity} {recipe.name} ...')
        response = await self.api.craft(recipe.code, quantity)
        if response:
            await self.inventory.update(recipe.code, quantity)
            for code, q_needed in recipe.items.items():
                await self.inventory.update(code, (q_needed * quantity * -1))
            #self.window.log(f'⚒️ {quantity} {recipe.name} created')
        return response

    async def gather(self) -> list[dict[str,Any]]:
        #self.window.log('⏳ Gathering ...')
        response = await self.api.gather()
        if response and 'details' in response:
            for d in response['details']['items']:
                drop = await self.inventory.update(d['code'], d['quantity'])
                d['name'] = drop.name if isinstance(drop, Item) else d['code']
            #drops_str = ", ".join([f"{d['quantity']}x {d['name']}" for d in response['details']['items']])
            #self.window.log(f"⛏️  Resource(s) gathered: {drops_str}")
            return response['details']['items']
        return []

    def __repr__(self) -> str:
        return f'{self.name}({self.role.className}:{self.level}) [❤️ {self.hp}/{self.max_hp}]'