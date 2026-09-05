import { useCharacters } from "../hooks/useCharacters";
import { CharacterTile } from "./CharacterTile";

export function CharacterList() {
    const { characters, loading, error } = useCharacters();

    if(loading) return <p>Loading...</p>
    if(error) return <p>Error: {error}</p>

    return <>
    <div className="characters">
        {characters.map((c) => (
            <CharacterTile key={c.name}
            data={c} />
        ))}
    </div>
    </>
}