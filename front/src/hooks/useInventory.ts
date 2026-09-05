import { useEffect, useState } from "react";
import type { Item } from "../types/item";
import * as Constants from '../constants'

export function useInventory(name: string) {
    const [Inventory, setInventory] = useState<Item[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        fetch(`${Constants.API_URL}/character/${name}/inventory`)
        .then((response) => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json()
        })
        .then((data: Item[]) => setInventory(data))
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false))
    }, []);

    return { Inventory, loading, error }
}