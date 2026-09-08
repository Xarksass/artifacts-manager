import { useInventoryFor } from "../contexts/InventoryContext";
import { ItemTile } from "./ItemTile";

export function InventoryList(props: { name: string }) {
    const { total, max, items} = useInventoryFor(props.name);

    if (items.length === 0) return <p>Inventaire vide.</p>;

    return <>
    <p>{total} / {max} items</p>
    <ul className="list-unstyled item-grid">
        {items.map((item) => { if (item.quantity) return (
            <li key={item.name}>
                <ItemTile item={item} />
            </li>
        )})}
    </ul>
    </>
}