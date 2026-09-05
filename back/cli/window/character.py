import asyncio
import curses
import math
from collections import deque
from collections.abc import Callable
from typing import TYPE_CHECKING

from core.logger import get_logger

if TYPE_CHECKING:
    from models.character import Character

import utils.dict_tools as dt

logger = get_logger(__name__,'character')

HEALTH_STATUS: dict[int,Callable[[int],bool]] = {
    curses.COLOR_CYAN: lambda h: h == 100,
    curses.COLOR_GREEN: lambda h: 50 < h < 100,
    curses.COLOR_YELLOW: lambda h: 20 < h <= 50,
    curses.COLOR_RED: lambda h: h <= 20,
}

class CharacterWindow:
    __action: str = 'idle'
    __height: int
    __width: int
    __logs: deque[str]
    __log_window: curses.window
    __status_window: curses.window
    __cooldown_window: curses.window

    def __init__(self, width: int, height: int, index: int, character: Character) -> None:
        self.__height = height
        self.__width = width
        self.__logs = deque([], maxlen=height - 2)
        self.character = character
        self.log_window = curses.newwin(height, width, height*index, width)
        self.status_window = self.log_window.derwin(1, 30, 0, 1)
        self.cooldown_window = self.log_window.derwin(1, 10, 0, width-11)
        curses.doupdate()

    @property
    def action(self) -> str: return self.__action

    @action.setter
    def action(self, action:str) -> None:
        self.__action = action
        self.refresh_status()

    @property
    def log_window(self) -> curses.window:
        return self.__log_window

    @log_window.setter
    def log_window(self, window: curses.window) -> None:
        self.__log_window = window
        self.__logs = deque([], maxlen=self.log_window.getmaxyx()[0] - 2)
        self.log_window.clear()
        self.log_window.border()
        self.log_window.noutrefresh()

    @property
    def status_window(self) -> curses.window:
        return self.__status_window

    @status_window.setter
    def status_window(self, window: curses.window) -> None:
        self.__status_window = window

    @property
    def cooldown_window(self) -> curses.window:
        return self.__cooldown_window

    @cooldown_window.setter
    def cooldown_window(self, window: curses.window) -> None:
        self.__cooldown_window = window

    def health_bar(self) -> str:
        section = ['█','▏','▎','▍','▌','▋','▊','▉']
        # 8 barres, chacune divisible en 8 niveaux -> résolution totale de 64
        units = round((self.character.hp / self.character.max_hp) * 64)
        if self.character.hp > 0:
            units = max(units, 1)  # toujours au moins 1/8 de visible tant qu'il reste de la vie
        full, rest = divmod(units, 8)
        bar = f'{section[0]*full}'
        if rest:
            bar += section[rest]
        return bar.ljust(8)

    def refresh_window(self):
        self.log_window.erase()
        self.log_window.border()
        for y, log in enumerate(self.__logs):
            self.log_window.addstr(y+1, 1, log)
        self.log_window.noutrefresh()
        curses.doupdate()
        self.refresh_status()

    def refresh_status(self):
        self.__status_window.erase()
        self.__status_window.addstr(0, 0, '┤')
        percentage = math.floor((self.character.hp / self.character.max_hp) * 100)
        self.__status_window.addstr(0, 1, f'{self.health_bar()}', curses.color_pair(dt.dict_match(HEALTH_STATUS,percentage)))
        status = f'| [{self.character.level}] {self.character.name} ├'.ljust(21,'─')
        try:
            self.__status_window.addstr(0, 9, status)
        except curses.error:
            pass
        self.__status_window.noutrefresh()
        curses.doupdate()


    def cooldown_bar(self, remaining: float, total: float) -> str:
        section = ['█','▏','▎','▍','▌','▋','▊','▉']
        if remaining == 0:
            bar = '─'*8
            return bar
        else:
            # 8 barres, chacune divisible en 8 niveaux -> résolution totale de 64
            units = round((remaining / total) * 64)
            if self.character.hp > 0:
                units = max(units, 1)  # toujours au moins 1/8 de visible tant qu'il reste de la vie
            full, rest = divmod(units, 8)
            bar = f'{section[0]*full}'
            if rest:
                bar += section[rest]
        return bar.ljust(8)

    def refresh_cooldown(self, remaining: float, total: float) -> None:
        self.cooldown_window.erase()
        bar = self.cooldown_bar(remaining, total)
        if remaining > 0:
            self.cooldown_window.addstr(0, 0, '┤')
            self.cooldown_window.addstr(0, 1, f'{bar}', curses.color_pair(curses.COLOR_CYAN))
            status = '├'
            try:
                self.__status_window.addstr(0, 9, status)
            except curses.error:
                pass
        else:
            try:
                self.cooldown_window.addstr(0, 0, bar)
            except curses.error:
                pass
        self.cooldown_window.noutrefresh()
        curses.doupdate()

    async def run_cooldown(self, stop_event: asyncio.Event, refresh_interval: float = 1.0,) -> None:
        loop = asyncio.get_running_loop()
        deadline = self.character.next_ready_at()

        if deadline:
            while True:
                remaining = deadline - loop.time()
                if stop_event.is_set():
                    break
                if remaining <= 0:
                    break
                self.refresh_cooldown(remaining, self.character.cooldown.remaining)
                # On dort jusqu'au prochain refresh OU jusqu'à l'expiration,
                # selon ce qui arrive en premier — évite de survoler la deadline
                # d'un tick entier sur les derniers instants du cooldown.
                await asyncio.sleep(min(refresh_interval, remaining))

            self.refresh_cooldown(0.0, self.character.cooldown.remaining)  # état final affiché avant de rendre la main

    def log(self, entry: str) -> None:
        self.__logs.append(entry)
        logger.info(entry)
        self.refresh_window()