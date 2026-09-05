import Stack from "react-bootstrap/esm/Stack";
import { useInventory } from "../hooks/useInventory";
import Badge from "react-bootstrap/esm/Badge";
import { useEffect, useState } from "react";
import * as Constants from '../constants'

export function InventoryList(name: string) {
    const { Inventory, loading, error } = useInventory(name);

    if(loading) return <p>Loading...</p>
    if(error) return <p>Error: {error}</p>

    const [itemList, setItemList] = useState(Inventory)
    
    // Mises à jour en continu via WebSocket
    useEffect(() => {
        const ws = new WebSocket(Constants.WS_URL);

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            if (message.type == "inventory_update") {
                setItemList(message.data)
            }
        };

        ws.onerror = (err) => console.error("WebSocket error", err);

        return () => ws.close();
    }, []);

    function item_img_src(code:string) {
        return "https://artifactsmmo.com/images/items/"+code+".png"
    }

    return <>
    <ul>
        {itemList.map((item) => (
            <li key={item.name}>
                <img src={ item_img_src(item.code) } alt={item.name}/>
                <Stack direction="horizontal" gap={2}>
                    {item.quantity}x {item.name} 
                    <Badge bg="success">{item.type}/{item.subtype}</Badge>
                    {item.crafting.map((skill) => ( <Badge bg="warning" text="dark">{skill}</Badge> ))}
                    {item.effects.map((effect) => ( <Badge bg="primary">{effect}</Badge> ))}
                </Stack>
            </li>
        ))}
    </ul>
    </>
}