import asyncio
import curses
import curses.textpad
from collections import deque

from cli.handlers.character import CharacterHandler
from commons.character import Character
from core.task_pool import TaskPool


class Navigation:
    __terminal: curses.window
    __window: curses.window
    __input: curses.window
    __input_lock: asyncio.Lock = asyncio.Lock()
    __logs: deque[str]
    characters: list[Character]
    pool: TaskPool

    def __init__(self, terminal: curses.window, window: curses.window, intput: curses.window, characters: list[Character]) -> None:
        self.__terminal = terminal
        self.__window = window
        self.__input = intput
        self.__logs = deque([], maxlen=self.terminal.getmaxyx()[0] - 2)
        self.characters = characters
        self.pool = TaskPool()

    @property
    def terminal(self) -> curses.window: return self.__terminal

    @property
    def window(self) -> curses.window: return self.__window

    @property
    def input(self) -> curses.window: return self.__input

    @property
    def input_lock(self) -> asyncio.Lock: return self.__input_lock

    @property
    def logs(self) -> deque[str]: return self.__logs

    def refresh_terminal(self) -> None:
        self.terminal.clear()
        self.terminal.border()

        for y, log in enumerate(self.logs):
            self.terminal.addstr(y+1, 1, log)
        self.terminal.noutrefresh()

        # focus back on the input window
        self.input.clear()
        self.input.noutrefresh()
        curses.doupdate()

    def log(self, entry: str) -> None:
        self.logs.append(entry)
        self.refresh_terminal()

    async def _read_input(self) -> str:
        self.input.clear()
        self.input.noutrefresh()
        curses.doupdate()

        loop = asyncio.get_event_loop()
        curses.flushinp()
        box = curses.textpad.Textbox(self.input)
        box.win.timeout(100) # type: ignore
        input = await loop.run_in_executor(None, box.edit)
        
        return input.strip()

    async def _listen_input(self):
        """ Handle textbx input when the player is waiting for his turn """
        while True:
            if not self.input_lock.locked():
                async with self.input_lock:
                    await asyncio.sleep(0.05)
                    input = await self._read_input()

                    if len(input) == 0:
                        continue

                    return input
            else:
                await asyncio.sleep(0.05)

    def is_valid(self, value: str, *, list: list[int] | None = None, max: int | None = None, skip: bool = False) -> bool:
        """
        Return true:
        - if the value is alphabetic and in the list ('q','quit','b','back')
        - if the value is numeric and in the range 0 < value <= max
            - if max is provided, and the value is in the range 0 < value <= max
            - if list is provided, and the value is in the provided list of valid values
        if none of previous condition is matched, return False
        """
        if value.isnumeric():
            if max:
                return (0 < int(value) <= max)
            elif list:
                return int(value) in list
        elif value.isalpha():
            return value in ('q','quit','b','back')
        elif skip:
            return not value
        return False 

    async def menu(self, options: list[str], title: str, ask: str, *, skip: bool = False) -> str:
        """
        Build a menu for the users to choose from the options.

        Will automatically parse the provided options to build the list of valid input
        and display the value to enter in cyan

        Args :
            - options: options to choose from
            - title : the title of the menu to display
            - ask: the question to prompt

        Returns the user input once valid
        """
        self.window.clear()
        self.window.border()
        y = 1
        self.window.addstr(y, 1, title, curses.color_pair(curses.COLOR_CYAN))

        for i, opt in enumerate(options):
            y += 1
            self.window.addstr(y ,1, f'{i+1}', curses.color_pair(curses.COLOR_CYAN))
            self.window.addstr(y, 3, opt)

        y += 2
        self.window.addstr(y, 1, 'q: quit | b: back')
        y += 1
        self.window.addstr(y, 1, ask, curses.color_pair(curses.COLOR_CYAN))
        self.window.noutrefresh()
        curses.doupdate()

        choice = 'None'
        max = len(options)
        while not self.is_valid(choice, max=max, skip=skip):
            choice = await self._listen_input()

            if not self.is_valid(choice, max=max, skip=skip):
                self.window.addstr('invalid_choice', curses.color_pair(curses.COLOR_RED))
        return choice

    async def run_menu(self):
        while True:
            options = [c.name for c in self.characters]
            choice = await self.menu(options,'Main menu','Select character')

            if choice.lower() in ('q','quit','b','back'):
                self.log("User asked to quit")
                self.log("Shutting down ...")
                await asyncio.sleep(1)
                return
            elif 0 < int(choice) <= len(options):
                handler = CharacterHandler(self,self.characters[int(choice)-1])
                await handler.charcter_menu()