import asyncio
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from cli.window.character import CharacterWindow
from commons.locations import Position
from dataclass.item import Item, Recipe
from endpoints.character import CharacterEndpoint
from endpoints.endpoint import Cooldown
from endpoints.maps import MapsEndpoint
from endpoints.monsters import MonstersEndpoint
from roles.role import Role

from .inventory import Inventory

IDLE = 'Idle.'

SKILLS = {
    "mining_level": "mining",
    "woodcutting_level": "woodcutting",
    "fishing_level": "fishing",
    "weaponcrafting_level": "weaponcrafting",
    "gearcrafting_level": "gearcrafting",
    "jewelrycrafting_level": "jewelrycrafting",
    "cooking_level": "cooking",
    "alchemy_level": "alchemy",
}

@dataclass
class Skills:
    mining: int = 1
    woodcutting: int = 1
    fishing: int = 1
    weaponcrafting: int = 1
    gearcrafting: int = 1
    jewelrycrafting: int = 1
    cooking: int = 1
    alchemy: int = 1

@dataclass
class HP:
    current: int
    max: int

class Character:
    name: str
    level: int
    gold: int
    inventory: Inventory
    skills: Skills
    hp: int
    max_hp: int
    pos: Position
    role: Role
    api: CharacterEndpoint
    logs: deque[str]
    _next_ready_at: float | None # deadline absolue (loop.time())
    __cooldown: Cooldown
    __window: CharacterWindow

    def __init__(self, name:str, level:int, hp:tuple[int,int], pos:tuple[int,int], skills: dict[str,int], inventory: list[dict[str,Any]]) -> None:
        self.name = name
        self.level = level
        self.hp = hp[0]
        self.max_hp = hp[1]
        self.pos = Position(*pos)
        self.inventory = Inventory(inventory)
        self.skills = Skills(**skills)
        self.api = CharacterEndpoint(self)
        self.role = Role(self)
        self._next_ready_at = None

    @property
    def window(self) -> CharacterWindow:
        return self.__window

    @window.setter
    def window(self, window: CharacterWindow) -> None:
        self.__window = window
        self.window.action = 'idle'

    @property
    def cooldown(self) -> Cooldown: return self.__cooldown

    @cooldown.setter
    def cooldown(self, cd: Cooldown) -> None:
        self.__cooldown = cd
        self._next_ready_at = asyncio.get_running_loop().time() + cd.remaining
        if cd.remaining:
            asyncio.create_task(self.window.run_cooldown(asyncio.Event()))

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

    async def move(self, mx:int, my:int) -> None:
        await self.move_to(self.pos.x + mx,self.pos.y + my)

    async def move_to(self, x:int, y:int) -> None:
        map_api = MapsEndpoint()
        from_details = map_api.get_cell_details(self.pos.x, self.pos.y)
        to_details = map_api.get_cell_details(x, y)

        from_name = f'{from_details['name']}'
        if 'interactions' in from_details:
            from_iter = from_details['interactions']['content']
            from_name += f' - {from_iter['code'].replace('_','').capitalize()}({from_iter['type'].replace('_','').capitalize()})'

        to_name = f'{to_details['name']}'
        if 'interactions' in to_details:
            to_iter = to_details['interactions']['content']
            to_name += f' - {to_iter['code'].replace('_','').capitalize()}({to_iter['type'].replace('_','').capitalize()})'

        self.window.log(f'Moving from {from_name} to {to_name}...')
        response = await self.api.move(x,y)
        if response:
            self.window.log(f'Moved from {from_name} to {to_name} on {response["destination"]['name']}.')
            self.pos = Position(x,y)

    async def fight(self) -> None:
        map_api = MapsEndpoint()
        map_details = map_api.get_cell_details(self.pos.x, self.pos.y)
        if 'interactions' in map_details:
            iter_type = map_details['interactions']['content']
            if iter_type['type'] == 'monster':
                monster_api = MonstersEndpoint()
                monster = monster_api.get_monster_details(iter_type['code'])
            
                self.window.log(f'Attacking {monster['name']}...')
                response = await self.api.fight()

                if response:
                    fight = response["fight"]
                    fight_stats = fight["characters"][0]
                    
                    self.window.log("🏆 Fight won!" if fight["result"] == "win" else "💀 Fight lost!")
                    self.window.log(f"⚔️  XP gained: {fight_stats['xp']} | HP remaining: {fight_stats['final_hp']}")
                    
                    if len(fight_stats["drops"]) > 0:
                        for d in fight_stats['drops']:
                            self.inventory.update(d['code'], d['quantity'])
                        drops_str = ", ".join([f"{d['quantity']}x {d['code']}" for d in fight_stats["drops"]])
                        self.window.log(f"🎁 Loot dropped: {drops_str}")

    async def rest(self) -> int:
        response = await self.api.rest()
        return response["hp_restored"]

    async def eat(self) -> int:
        cooked_food = self.inventory.pick(itemtype='consumable',subtype=['food'], effect='heal')

        if cooked_food:
            to_eat, diff = self.select_best_heal_item(cooked_food)
            hp_restored = self.max_hp - self.hp - diff
            
            if to_eat is not None:
                self.window.log(f'Eating a portion of {to_eat.name}...')
                await self.api.use(to_eat.code)
                self.window.log(f'1 portion of {to_eat.name} eaten.')
                return hp_restored
        return 0

    async def drink(self) -> int:
        potions = self.inventory.pick(itemtype='consumable',subtype=['potion'], effect='heal')

        if potions:
            to_drink, diff = self.select_best_heal_item(potions)
            hp_restored = self.max_hp - self.hp - diff
            
            if to_drink is not None:
                self.window.log(f'Drinking {to_drink.name}...')
                await self.api.use(to_drink.code)
                self.window.log(f'1 {to_drink.name} drank.')
                return hp_restored
        return 0

    async def heal(self) -> None:
        hp_restored = 0

        if self.inventory.pick(itemtype='consumable',subtype=['potion']):
            hp_restored = await self.drink()

        if not hp_restored and self.inventory.pick(itemtype='consumable',subtype=['food']):
            hp_restored = await self.eat()

        if not hp_restored:
            hp_restored = await self.rest()

        self.window.log(f"Restored {hp_restored} HP.")
        self.window.log(f"❤️ Current HP: {self.hp}/{self.max_hp}")

    async def craft(self, item:str, quantity:int = 1) -> dict[str,Any]:
        self.window.log(f'Crafting {quantity} {item} ...')
        response = await self.api.craft(item, quantity)
        if response:
            self.window.log(f'{quantity} {item} created')
        return response

    async def gather(self) -> None:
        self.window.log('Gathering ...')
        response = await self.api.gather()
        if response and 'details' in response:
            for d in response['details']['items']:
                self.window.log(f'{d['quantity']}x {d['code']} gathered')

    """ Bank actions"""
    async def store(self, item:str, quantity: int|str) -> None:
        if quantity == 'all':
            quantity = self.inventory.items[item].quantity

        assert isinstance(quantity, int)
        self.window.log(f"Store {quantity} {item} into the bank...")
        response = await self.api.store(item, quantity)
        if response:
            self.inventory.update(item, -(quantity))
            self.window.log(f"Stored {quantity} {item} into the bank")

    def check_bank_item_type(self, type:str, subtype:str) -> bool: return False

    def __repr__(self) -> str:
        return f'{self.name}({self.role.className}:{self.level}) [❤️ {self.hp}/{self.max_hp}]'