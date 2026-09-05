from datetime import datetime
from typing import NamedTuple


class Cooldown(NamedTuple):
    remaining: int
    expiration: datetime