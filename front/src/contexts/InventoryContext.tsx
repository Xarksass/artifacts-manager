import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";
import type { Inventory } from "../types/inventory";
import { useWebSocketMessage } from "./WebSocketContext";
import * as Constants from "../constants";

type InventoryMap = Record<string, Inventory>;

const EMPTY_INVENTORY: Inventory = { total: 0, max: 100, items: [] };

const InventoryContext = createContext<InventoryMap>({});

export function InventoryProvider(props: { characterNames: string[]; children: ReactNode }) {
    const [inventories, setInventories] = useState<InventoryMap>({});

    // Précharge l'inventaire de chaque personnage dès que la liste est connue
    useEffect(() => {
        props.characterNames.forEach((name) => {
            fetch(`${Constants.API_URL}/character/${encodeURIComponent(name)}/inventory`)
                .then((res) => {
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    return res.json();
                })
                .then((inventory: Inventory) => {
                    setInventories((prev) => ({ ...prev, [name]: inventory }));
                })
                .catch((err) => console.error(`Inventory fetch failed for ${name}`, err));
        });
    }, [props.characterNames]);

    const handleMessage = useCallback((message: any) => {
        if (message.type !== "inventory_update") return;
        setInventories((prev) => ({ ...prev, [message.name]: message.data }));
    }, []);

    useWebSocketMessage(handleMessage);

    return (
        <InventoryContext.Provider value={inventories}>
            {props.children}
        </InventoryContext.Provider>
    );
}

export function useInventoryFor(name: string): Inventory {
    const inventories = useContext(InventoryContext);
    return inventories[name] ?? EMPTY_INVENTORY;
}