// src/hooks/useActiveRoutines.ts
import { useEffect, useState } from "react";
import * as Constants from '../constants'

export function useActiveRoutines() {
    const [activeRoutines, setActiveRoutines] = useState<string[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        fetch(`${Constants.API_URL}/character/routines/active`)
        .then((response) => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json()
        })
        .then((data: string[]) => setActiveRoutines(data))
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false))
    }, []);

    return { activeRoutines, loading, error }
}