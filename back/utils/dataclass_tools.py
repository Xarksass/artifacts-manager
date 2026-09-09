from dataclasses import fields, is_dataclass
from typing import Any


def diff_and_update(target: Any, source: Any) -> set[str]:
    """
    Met à jour `target` en place avec les valeurs de `source` (même type de dataclass).
    Retourne l'ensemble des noms de champs top-level modifiés (récursif sur les
    dataclasses imbriquées, mais le nom retourné reste celui du champ parent,
    ex: 'res' si res.fire a changé).
    """
    changed:set[str] = set()
    for f in fields(target):
        old_val = getattr(target, f.name)
        new_val = getattr(source, f.name)

        if is_dataclass(old_val) and is_dataclass(new_val):
            if diff_and_update(old_val, new_val):
                changed.add(f.name)
        elif old_val != new_val:
            setattr(target, f.name, new_val)
            changed.add(f.name)

    return changed