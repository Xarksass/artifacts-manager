import { useCallback, useEffect, useRef, useState } from 'react';
import { useWebSocketMessage } from "../contexts/WebSocketContext";

export function CooldownBar(props: { name: string; initialExpiration: string | null }) {
    const [duration, setDuration] = useState('0s');
    const [width, setWidth] = useState('0%');
    const barRef = useRef(null);

    useEffect(() => {
        if (!props.initialExpiration) return;
        const remaining = (new Date(props.initialExpiration).getTime() - Date.now()) / 1000;
        if (remaining <= 0) return;

        setDuration('0s');
        setWidth('100%');
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                setDuration(`${remaining}s`);
                setWidth('0%');
            });
        });
    }, []); // uniquement au montage

    const handleMessage = useCallback((message: any) => {
        if (message.name !== props.name) return;
        if (message.type === "cooldown_update") {
            // 1. Reset instantané à 100% SANS transition
            setDuration('0s');
            setWidth('100%');

            // 2. Attendre que le navigateur applique bien le 100% avant de lancer la transition
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    setDuration(`${message.data}s`); // en secondes pour CSS
                    setWidth('0%');
                });
            });
        };
    }, [props.name]);

    useWebSocketMessage(handleMessage);

    return <>
        <div ref={barRef} className="cooldown" style={{ '--cd': width, '--cd-duration': `${duration}` } as React.CSSProperties} ></div>
    </>;
}