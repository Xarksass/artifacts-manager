import { useEffect, useState } from "react";
import type { Item } from "../types/item";
import * as Constants from '../constants'

export function useBank() {
    const [bank, setBank] = useState<Item[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        fetch(`${Constants.API_URL}/bank/`)
        .then((response) => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json()
        })
        .then((data: Item[]) => setBank(data))
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false))
    }, []);

    return { bank, loading, error }
}