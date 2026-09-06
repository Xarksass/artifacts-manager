import Stack from "react-bootstrap/esm/Stack";
import Badge from "react-bootstrap/esm/Badge";
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Popover from 'react-bootstrap/Popover';
import type { Item } from "../types/item";

function item_img_src(code:string) {
    return "https://artifactsmmo.com/images/items/"+code+".png"
}
function effect_img_src(code:string) {
    return "https://artifactsmmo.com/images/effects/"+code+".png"
}

export function ItemTile(props: { item: Item }) {
    const item = props.item

    return <>
        <div className="item">
            <OverlayTrigger
                trigger={["hover","focus"]}
                key="bottom"
                placement="bottom"
                overlay={
                    <Popover id={`popover-${item.name}`}>
                    <Popover.Header as="h3">{item.name} <Badge bg="success">{item.type}/{item.subtype}</Badge></Popover.Header>
                    <Popover.Body>
                        <Stack gap={2}>
                            {/* <small>{item.effects.map((effect) => ( <img className="img-fluid" src={effect_img_src(effect)} alt={effect} /> ))}</small> */}
                            {item.effects.map((effect) => ( <Badge key={effect} bg="danger">{effect}</Badge> ))}
                            {item.crafting.map((skill) => ( <Badge key={skill} bg="warning" text="dark">{skill}</Badge> ))}
                        </Stack>
                    </Popover.Body>
                    </Popover>
                }
            >
                <figure>
                    <img className="img-fluid" src={ item_img_src(item.code) } alt={item.name}/>
                    <div className="quantity">{item.quantity}</div>
                </figure>
            </OverlayTrigger>
        </div>
    </>
}