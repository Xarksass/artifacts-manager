from dataclasses import dataclass

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