export interface Character {
    name: string
    level: number
    hp: number
    max_hp: number
    xp: number
    max_xp: number
    x: number
    y: number
    skin: string
    cooldown_expiration: string | null
}