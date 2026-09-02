import asyncio
import curses

#from asyncio import Task
from collections import deque
from typing import Any

from cli.menu import Navigation
from cli.window.character import CharacterWindow
from commons.bank import Bank
from core.logger import get_logger
from endpoints.characters import CharactersEndpoint

logger = get_logger(__name__,'main')

characters_endpoint = CharactersEndpoint()

logs: deque[str]|None = None

# Lock and Threads
stop_event = asyncio.Event()

# Curses windows
terminal: curses.window|None = None
input_win: curses.window|None = None

input_listener: asyncio.Task[Any]|None = None

bank: Bank|None = None

# Utility: display the stored messages and refresh the msg window
def refresh_terminal() -> None:
    assert logs is not None
    assert terminal is not None

    terminal.clear()
    terminal.border()
    for y, log in enumerate(logs):
        terminal.addstr(y+1, 1, log)
    terminal.refresh()

    # focus back on the input window
    if input_win is not None:
        input_win.clear()
        input_win.refresh()

def log(entry: str) -> None:
    assert logs is not None
    logger.info(entry)
    logs.append(entry)
    refresh_terminal()

async def main(screen: curses.window):
    global bank, input_win, logs, terminal
    logger.debug('Initialise curses ...')

    screen.clear()
    screen.refresh()

    curses.init_pair(curses.COLOR_CYAN,
                        curses.COLOR_CYAN,
                        curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_GREEN,
                        curses.COLOR_GREEN,
                        curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_YELLOW,
                        curses.COLOR_YELLOW,
                        curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_RED,
                        curses.COLOR_RED,
                        curses.COLOR_BLACK)
    
    win_width = curses.COLS // 2

    terminal = curses.newwin(curses.LINES, win_width, 0, 0)
    terminal.border()

    logs = deque([], maxlen=terminal.getmaxyx()[0] - 2)

    log('Bank Syncronisation ...')
    bank = Bank()
    log('Bank Synced ! ✔️')

    log('Loading Characters ...')
    characters = await characters_endpoint.get_characters()
    log('Characters loaded! ✔️')

    await asyncio.sleep(1)

    win_height = curses.LINES // 5

    logger.debug("Creating characters' windows ...")
    for index, character in enumerate(characters):
        character.window = CharacterWindow(win_width, win_height, index, character)

    half_height = curses.LINES // 2

    logger.debug("Resizing terminal ...")
    terminal.clear()
    terminal.refresh()

    terminal.resize(half_height,win_width)
    terminal.border()
    terminal.refresh()

    logger.debug("Creating menu terminal ...")
    menu = curses.newwin(half_height - 1, win_width, half_height, 0)
    menu.border()
    menu.refresh()

    logger.debug("Creating input ...")
    # Input window, used to handle interactive input
    input_win = curses.newwin(1, win_width, curses.LINES - 2, 0)

    logger.debug("Initialise navigation ...")
    navigation = Navigation(terminal, menu, input_win, characters)

    logger.debug("Starting navigation")
    await navigation.run_menu()

if __name__ == "__main__":
    curses.wrapper(lambda screen: asyncio.run(main(screen)))