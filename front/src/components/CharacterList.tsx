import { useCharacters } from "../hooks/useCharacters";
import { useActiveRoutines } from "../hooks/useActiveRoutines";
import { CharacterTile } from "./CharacterTile";
import { InventoryProvider } from "../contexts/InventoryContext";

export function CharacterList() {
    const { characters, loading, error } = useCharacters();
    const { activeRoutines, loading: routinesLoading } = useActiveRoutines();

    if(loading || routinesLoading) return <p>Loading...</p>
    if(error) return <p>Error: {error}</p>

    return <>
    <InventoryProvider characterNames={characters.map((c) => c.name)}>
        <div className="characters">
            {characters.map((c) => (
                <CharacterTile key={c.name}
                data={c}
                initiallyActive={activeRoutines.includes(c.name)} />
            ))}
        </div>
    </InventoryProvider>
    </>
}