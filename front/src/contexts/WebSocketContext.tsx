import { createContext, useContext, useEffect, useRef, type ReactNode } from "react";
import * as Constants from "../constants";

type MessageHandler = (message: any) => void;

interface WebSocketContextValue {
    subscribe: (handler: MessageHandler) => () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function WebSocketProvider({ children }: { children: ReactNode }) {
    const handlers = useRef<Set<MessageHandler>>(new Set());

    useEffect(() => {
        const ws = new WebSocket(Constants.WS_URL);

        ws.onopen = () => console.log("WS connecté ✔️");

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            handlers.current.forEach((handler) => handler(message));
        };

        ws.onerror = (err) => console.error("WebSocket error", err);

        return () => ws.close();
    }, []);

    function subscribe(handler: MessageHandler) {
        handlers.current.add(handler);
        return () => handlers.current.delete(handler);
    }

    return (
        <WebSocketContext.Provider value={{ subscribe }}>
            {children}
        </WebSocketContext.Provider>
    );
}

export function useWebSocketMessage(onMessage: MessageHandler) {
    const ctx = useContext(WebSocketContext);
    if (!ctx) throw new Error("useWebSocketMessage must be used within WebSocketProvider");

    useEffect(() => {
        return ctx.subscribe(onMessage);
    }, [ctx, onMessage]);
}