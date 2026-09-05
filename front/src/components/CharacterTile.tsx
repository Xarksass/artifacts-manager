import { useEffect, useState } from "react";
import type { Character } from "../types/character";
import * as Constants from '../constants'

export function CharacterTile(props: { data: Character }) {
    //const [character, setCharacter] = useState(data)
    const [character, setCharacter] = useState(props.data)

    // Mises à jour en continu via WebSocket
    useEffect(() => {
        const ws = new WebSocket(Constants.WS_URL);

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type == "character_update" && message.data.name == character.name) {
                setCharacter(message.data)
            }
        };

        ws.onerror = (err) => console.error("WebSocket error", err);

        return () => ws.close();
    }, []);


    function skin_src(code: string) {
        return `https://artifactsmmo.com/images/characters/${code}.png`
    }
    
    async function startRoutine(name: string): Promise<void> {
        const res = await fetch(`${Constants.API_URL}/character/${encodeURIComponent(name)}/routine`, {
            method: "PATCH",
        });
        if (!res.ok) {
            const body = await res.text();
            console.error(`Échec démarrage routine (${res.status})`, body);
        }
    }

    return <>
    <div className="character panel" key={character.name}>
        <div className="cooldown"></div>
        <div className="repr">
            <div className="desc">
                <div className="name">{character.name} <small>({character.x},{character.y})</small></div>
                <div className="level">Lvl {character.level}</div>
            </div>
            <div className="skin">
                <img src={skin_src(character.skin)} alt={character.name} />
            </div>
            <div className="stats">
                <div className="health">{character.hp}/{character.max_hp} HP</div>
                <div className="exp">{character.xp}/{character.max_xp} XP</div>
            </div>
        </div>
        <button onClick={() => startRoutine(character.name)}>Start routine</button>
        {/* <div className="logs"></div> */}
    </div>
    </>
}