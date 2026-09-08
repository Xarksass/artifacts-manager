import { useCallback, useEffect, useRef, useState } from "react";
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Tooltip from 'react-bootstrap/Tooltip';
import Popover from 'react-bootstrap/Popover';
import { CooldownBar } from "./CooldownBar"
import { InventoryModal } from "./InventoryModal";
import type { Character } from "../types/character";
import { useWebSocketMessage } from "../contexts/WebSocketContext";
import * as Constants from '../constants'
import Button from "react-bootstrap/esm/Button";
import Spinner from "react-bootstrap/esm/Spinner";

export function CharacterTile(props: { data: Character; initiallyActive: boolean }) {
    const [character, setCharacter] = useState(props.data)
    const [logs, setLogs] = useState<string[]>([])
    const [routineActive, setRoutineActive] = useState(props.initiallyActive)

    const logsRef = useRef<HTMLDivElement>(null);
    const isHovering = useRef(false);

    useEffect(() => {
        fetch(`${Constants.API_URL}/character/${encodeURIComponent(character.name)}/logs`)
            .then((res) => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then((data: string[]) => setLogs(data))
            .catch((err) => console.error(`Échec chargement des logs`, err));
    }, []);

    const handleMessage = useCallback((message: any) => {
        if (message.name !== character.name) return;
        if (message.type === "character_update") setCharacter(message.data);
        if (message.type === "log_update") setLogs(message.data);
    }, [character.name]);

    useWebSocketMessage(handleMessage);

    // Auto-scroll vers le bas à chaque nouveau log, sauf si la souris est dessus
    useEffect(() => {
        if (!isHovering.current && logsRef.current) {
            logsRef.current.scrollTop = logsRef.current.scrollHeight;
        }
    }, [logs]);

    function handleMouseEnter() {
        isHovering.current = true;
    }
    function handleMouseLeave() {
        isHovering.current = false;
        if (logsRef.current) {
            logsRef.current.scrollTop = logsRef.current.scrollHeight;
        }
    }

    function skin_src(code: string) {
        return `https://artifactsmmo.com/images/characters/${code}.png`
    }
    function barValue(val: number, max: number) {
        return `${ Math.round((val/ max)*100) }%`
    }
    
    async function rest(name: string): Promise<void> {
        const res = await fetch(`${Constants.API_URL}/character/${encodeURIComponent(name)}/rest`, {
            method: "PATCH"
        });
        if (!res.ok) {
            const body = await res.text();
            console.error(`Échec repos (${res.status})`, body);
        }
    }
    async function startRoutine(name: string, role: string): Promise<void> {
        const res = await fetch(`${Constants.API_URL}/character/${encodeURIComponent(name)}/routine/start`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({name: role})
        });
        if (!res.ok) {
            const body = await res.text();
            console.error(`Échec démarrage routine (${res.status})`, body);
            return;
        }
        setRoutineActive(true);
    }
    async function stopRoutine(name: string): Promise<void> {
        const res = await fetch(`${Constants.API_URL}/character/${encodeURIComponent(name)}/routine/stop`, {
            method: "PATCH"
        });
        if (!res.ok) {
            const body = await res.text();
            console.error(`Échec arrêt routine (${res.status})`, body);
            return;
        }
        setRoutineActive(false);
    }

    return <>
    <div className="character panel" key={character.name}>
        <div className="repr">
            <CooldownBar name={character.name} initialExpiration={character.cooldown_expiration} />
            <div className="desc">
                <div className="name">{character.name}{/* <small>({character.x},{character.y})</small> */}</div>
                <div className="level"><small>lvl</small> <b>{character.level}</b></div>
            </div>
            <div className="skin">
                <img src={skin_src(character.skin)} alt={character.name} />
            </div>
            <div className="stats-actions">
                <div className="stats">
                    <div className="health" style={{ '--bar-value': barValue(character.hp, character.max_hp) } as React.CSSProperties}>{character.hp}/{character.max_hp} HP</div>
                    <OverlayTrigger
                        placement="bottom"
                        delay={{ show: 250, hide: 400 }}
                        overlay={
                            <Tooltip id="button-tooltip">{character.xp}/{character.max_xp} XP</Tooltip>
                        }
                    >
                        <div className="exp" style={{ '--bar-value': barValue(character.xp, character.max_xp) } as React.CSSProperties}></div>
                    </OverlayTrigger>
                </div>
                <ul className="list-unstyled action-list">
                    <li>
                        <OverlayTrigger placement="bottom" delay={{ show: 250, hide: 400 }} overlay={ <Tooltip>Equipment</Tooltip> }>
                            <Button variant="outline-light"><span className="ico ico-armor"></span></Button>
                        </OverlayTrigger>
                    </li>
                    <li>
                        <OverlayTrigger placement="bottom" delay={{ show: 250, hide: 400 }} overlay={ <Tooltip>Stats</Tooltip> }>
                            <Button variant="outline-light"><span className="ico ico-character"></span></Button>
                        </OverlayTrigger>
                    </li>
                    <li>
                        <InventoryModal characterName={character.name} />
                    </li>
                    <li>
                        <OverlayTrigger placement="bottom" delay={{ show: 250, hide: 400 }} overlay={ <Tooltip>Rest</Tooltip> }>
                            <Button variant="outline-light" onClick={() => rest(character.name)}><span className="ico ico-rest"></span></Button>
                        </OverlayTrigger>
                    </li>
                    <li>
                        {routineActive ? (
                            <OverlayTrigger placement="bottom" delay={{ show: 250, hide: 400 }} overlay={ <Tooltip>Stop routine</Tooltip> }>
                                <Button variant="outline-light" onClick={() => stopRoutine(character.name)}>
                                    <Spinner animation="grow" size="sm" variant="light" />
                                </Button>
                            </OverlayTrigger>
                        ) : (
                            <OverlayTrigger
                                trigger="click"
                                key="bottom"
                                placement="bottom"
                                overlay={
                                    <Popover className="role-popover">
                                        <Popover.Header as="h3">Choose a Role</Popover.Header>
                                        <Popover.Body>
                                            <ul className="list-unstyled role-list">
                                                {/* <li>
                                                    <Button variant="outline-light" onClick={() => startRoutine(character.name, 'Artisan')} title="Artisan" disabled><span className="ico ico-artisan"></span></Button>
                                                </li>
                                                <li>
                                                    <Button variant="outline-light" onClick={() => startRoutine(character.name, 'Cook')} title="Cook"><span className="ico ico-cook"></span></Button>
                                                </li> */}
                                                <li>
                                                    <Button variant="outline-light" onClick={() => startRoutine(character.name, 'Miner')} title="Miner"><span className="ico ico-pickaxe"></span></Button>
                                                </li>
                                                <li>
                                                    <Button variant="outline-light" onClick={() => startRoutine(character.name, 'Lumberjack')} title="Lumberjack"><span className="ico ico-axe"></span></Button>
                                                </li>
                                                <li>
                                                    <Button variant="outline-light" onClick={() => startRoutine(character.name, 'Fisherman')} title="Fisherman"><span className="ico ico-fishing-hook"></span></Button>
                                                </li>
                                                <li>
                                                    <Button variant="outline-light" onClick={() => startRoutine(character.name, 'Picker')} title="Picker"><span className="ico ico-gatherer"></span></Button>
                                                </li>
                                                <li>
                                                    <Button variant="outline-light" onClick={() => startRoutine(character.name, 'Hunter')} title="Hunter"><span className="ico ico-hunter"></span></Button>
                                                </li>
                                            </ul>
                                        </Popover.Body>
                                    </Popover>
                                }
                            >
                                {/* <button className="btn btn-action"><span className="ico ico-role"></span></button> */}
                                <Button variant="outline-light"><span className="ico ico-role"></span></Button>
                            </OverlayTrigger>
                        )}
                    </li>
                </ul>
            </div>
        </div>
        <div className="logs custom-scroll"
            ref={logsRef}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}>
            <ul className="list-unstyled">
                {logs.map((log, i) => (
                    <li key={`log_${i}`}>{log}</li>
                ))}
            </ul>
        </div>
    </div>
    </>
}