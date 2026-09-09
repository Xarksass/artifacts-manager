from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from schemas.location import Position

SKILLS = {
    "mining_level",
    "woodcutting_level",
    "fishing_level",
    "weaponcrafting_level",
    "gearcrafting_level",
    "jewelrycrafting_level",
    "cooking_level",
    "alchemy_level",
}

@dataclass
class SkillsSchema:
    mining_level: int = 1
    woodcutting_level: int = 1
    fishing_level: int = 1
    weaponcrafting_level: int = 1
    gearcrafting_level: int = 1
    jewelrycrafting_level: int = 1
    cooking_level: int = 1
    alchemy_level: int = 1

    @staticmethod
    def from_json(json: dict[str,Any]) -> SkillsSchema:
        return SkillsSchema(
            json["mining_level"],
            json["woodcutting_level"],
            json["fishing_level"],
            json["weaponcrafting_level"],
            json["gearcrafting_level"],
            json["jewelrycrafting_level"],
            json["cooking_level"],
            json["alchemy_level"],
        )

@dataclass
class ElementaryStat:
    fire: int
    earth: int
    water: int
    air: int

@dataclass
class EntitySchema:
    name: str
    level: int
    hp: int
    critical_strike: int
    initiative: int
    attack: ElementaryStat
    res: ElementaryStat

@dataclass
class EquipementSchema:
    weapon: str
    rune: str
    shield: str
    helmet: str
    body_armor: str
    leg_armor: str
    boots: str
    ring1: str
    ring2: str
    amulet: str
    artifact1: str
    artifact2: str
    artifact3: str
    utility1: str
    utility1_quantity: int
    utility2: str
    utility2_quantity: int
    bag: str

    @staticmethod
    def from_json(json: dict[str,Any]) -> EquipementSchema:
        return EquipementSchema(
            json['weapon_slot'],
            json['rune_slot'],
            json['shield_slot'],
            json['helmet_slot'],
            json['body_armor_slot'],
            json['leg_armor_slot'],
            json['boots_slot'],
            json['ring1_slot'],
            json['ring2_slot'],
            json['amulet_slot'],
            json['artifact1_slot'],
            json['artifact2_slot'],
            json['artifact3_slot'],
            json['utility1_slot'],
            json['utility1_slot_quantity'],
            json['utility2_slot'],
            json['utility2_slot_quantity'],
            json['bag_slot'],
        )

@dataclass
class QuestSchema:
    task: str
    type: str
    progress: int
    total: int

    @staticmethod
    def from_json(json: dict[str,Any]) -> QuestSchema:
        return QuestSchema(
            json['task'],
            json['task_type'],
            json['task_progress'],
            json['task_total'],
        )

@dataclass
class CharacterSchema(EntitySchema):
    skin: str
    max_hp: int
    xp: int
    max_xp: int
    gold: int
    skills: SkillsSchema
    pos: Position
    speed: int
    haste: int
    wisdom: int
    prospecting: int
    threat: int
    base_dmg: int
    dmg: ElementaryStat
    equipment: EquipementSchema
    quest: QuestSchema|None

    @staticmethod
    def from_json(json: dict[str,Any]) -> CharacterSchema:
        return CharacterSchema (
            name = json['name'],
            level = json['level'],
            hp = json['hp'],
            max_hp = json['max_hp'],
            xp = json['xp'],
            max_xp = json['max_xp'],
            gold = json['gold'],
            skin = json['skin'],
            pos = Position(json['x'],json['y']),
            speed = json['speed'],
            haste = json['haste'],
            wisdom = json['wisdom'],
            prospecting = json['prospecting'],
            critical_strike = json['critical_strike'],
            initiative = json['initiative'],
            threat = json['threat'],
            base_dmg = json['dmg'],
            dmg = ElementaryStat(
                json['dmg_fire'],
                json['dmg_earth'],
                json['dmg_water'],
                json['dmg_air'],
            ),
            attack = ElementaryStat(
                json['attack_fire'],
                json['attack_earth'],
                json['attack_water'],
                json['attack_air'],
            ),
            res = ElementaryStat(
                json['res_fire'],
                json['res_earth'],
                json['res_water'],
                json['res_air'],
            ),
            skills = SkillsSchema.from_json(json),
            equipment = EquipementSchema.from_json(json),
            quest = QuestSchema.from_json(json)
        )


@dataclass
class MonsterSchema(EntitySchema):
    code: str
    type: str
    drops: list[str]

    @staticmethod
    def from_json(json: dict[str,Any]) -> MonsterSchema:
        return MonsterSchema(
            code = json['code'],
            name = json['name'], 
            level = json['level'], 
            type = json['type'], 
            hp = json['hp'],  
            attack = ElementaryStat(
                json["attack_fire"],
                json["attack_earth"],
                json["attack_water"],
                json["attack_air"],
            ),
            res = ElementaryStat(
                json["res_fire"],
                json["res_earth"],
                json["res_water"],
                json["res_air"],
            ),
            critical_strike = json['critical_strike'],
            initiative = json['initiative'],
            drops = [d['code'] for d in json['drops']],
        )