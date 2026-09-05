import { useEffect, useState } from "react";
import type { Character } from "../types/character";
import * as Constants from '../constants'

export function useCharacters() {
    const [characters, setCharacters] = useState<Character[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        fetch(`${Constants.API_URL}/character/all`)
        .then((response) => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json()
        })
        .then((data: Character[]) => setCharacters(data))
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false))
    }, []);

    return { characters, loading, error }
}