import asyncio
import sys
from typing import TYPE_CHECKING

from roles.cook import Cook
from roles.hunter import Hunter
from roles.role import Role

if TYPE_CHECKING:
    from cli.menu import Navigation
    from commons.character import Character

class CharacterHandler:
    __nav: Navigation
    character: Character

    def __init__(self, navigation: Navigation, character: Character) -> None:
        self.__nav = navigation
        self.character = character

    @property
    def nav(self) -> Navigation: return self.__nav

    async def assign_role(self):
        while True:
            Roles: dict[str,type[Role]] = {
                'Hunter': Hunter,
                'Cook': Cook,
            }
            options = list(Roles.keys())

            choice = await self.nav.menu(options,'Role menu',f'Select role for {self.character.name}')

            if choice.lower() in ('q','quit'):
                self.nav.log("User asked to quit")
                self.nav.log("Shutting down ...")
                await asyncio.sleep(1)
                sys.exit()
            if choice.lower() in ('b','back'):
                return
            else:
                self.character.role = Roles[options[int(choice)-1]](self.character)
                return
                

    async def charcter_menu(self):
        while True:
            if self.nav.pool.is_running(self.character.name):
                options = ['Stop routine']
            else:
                options = ['Assign role',]
                if self.character.role.className != 'Peasant':
                    options.append('Start routine')

            choice = await self.nav.menu(options,'Character menu',f'Select action for {self.character.name} ({self.character.role.className})')

            if choice.lower() in ('q','quit'):
                self.nav.log("User asked to quit")
                self.nav.log("Shutting down ...")
                await asyncio.sleep(1)
                sys.exit()
            if choice.lower() in ('b','back'):
                return
            elif 0 < int(choice) <= len(options):
                if self.nav.pool.is_running(self.character.name) and choice == '1':
                    await self.nav.pool.stop_and_wait(self.character.name)
                else:
                    if choice == '1':
                        await self.assign_role()
                    elif self.character.role.className != 'Peasant' and choice == '2':
                        self.nav.pool.start(self.character.name,self.character.role.routine)