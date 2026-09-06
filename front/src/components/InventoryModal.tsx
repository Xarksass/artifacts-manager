import { useState } from "react";
import Button from "react-bootstrap/esm/Button";
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Tooltip from 'react-bootstrap/Tooltip';
import Modal from "react-bootstrap/esm/Modal";
import { InventoryList } from "./InventoryList";

export function InventoryModal(props: { characterName: string }) {
    const [show, setShow] = useState(false);

    return (
        <>
            <OverlayTrigger placement="bottom" delay={{ show: 250, hide: 400 }} overlay={ <Tooltip>Inventory</Tooltip> }>
                <Button variant="outline-light" onClick={() => setShow(true)}><span className="ico ico-backpack"></span></Button>
            </OverlayTrigger>
            <Modal className="inventory-modal" size="lg" show={show} onHide={() => setShow(false)} centered>
                <Modal.Header closeButton>
                    <Modal.Title>Inventaire — {props.characterName}</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <InventoryList name={props.characterName} />
                </Modal.Body>
            </Modal>
        </>
    );
}