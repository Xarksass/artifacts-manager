from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass
class Task:
    name: str
    condition: Callable[[], bool]
    action: Callable[[], Awaitable[None]]