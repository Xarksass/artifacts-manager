import Stack from "react-bootstrap/esm/Stack";
import { useBank } from "../hooks/useBank";
import Badge from "react-bootstrap/esm/Badge";

export function BankList() {
    const { bank, loading, error } = useBank();

    if(loading) return <p>Loading...</p>
    if(error) return <p>Error: {error}</p>

    function item_img_src(code:string) {
        return "https://artifactsmmo.com/images/items/"+code+".png"
    }

    return <>
    <ul>
        {bank.map((item) => (
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