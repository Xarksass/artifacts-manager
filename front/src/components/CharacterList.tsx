import { useCharacters } from "../hooks/useCharacters";
import { CharacterTile } from "./CharacterTile";
import { InventoryProvider } from "../contexts/InventoryContext";

export function CharacterList() {
    const { characters, loading, error } = useCharacters();

    if(loading) return <p>Loading...</p>
    if(error) return <p>Error: {error}</p>

    return <>
    <InventoryProvider characterNames={characters.map((c) => c.name)}>
        <div className="characters">
            {characters.map((c) => (
                <CharacterTile key={c.name}
                data={c} />
            ))}
        </div>
    </InventoryProvider>
    </>
}