import { useCallback, useState } from "react";
import { CooldownBar } from "./CooldownBar"
import type { Character } from "../types/character";
import { useWebSocketMessage } from "../contexts/WebSocketContext";
import * as Constants from '../constants'

export function CharacterTile(props: { data: Character }) {
    //const [character, setCharacter] = useState(data)
    const [character, setCharacter] = useState(props.data)
    const [logs, setLogs] = useState<string[]>([])

    const handleMessage = useCallback((message: any) => {
        if (message.name !== character.name) return;
        if (message.type === "character_update") setCharacter(message.data);
        if (message.type === "log_update") setLogs(message.data);
    }, [character.name]);

    useWebSocketMessage(handleMessage);

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
        <CooldownBar name={character.name} />
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
        <div className="logs">
            <ul>
                {logs.map((log, i) => (
                    <li key={`log_${i}`}>{log}</li>
                ))}
            </ul>
        </div>
    </div>
    </>
}