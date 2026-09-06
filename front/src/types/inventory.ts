import type { Item } from "./item";

export interface Inventory {
    total: number
    max: number
    items: Item[]
}