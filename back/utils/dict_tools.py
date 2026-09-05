from collections.abc import Callable
from typing import Any, overload


class DictMatchException(Exception): pass

@overload
def dict_match(dict_match:dict[str,Callable[[Any],bool]], value:Any) -> str: ...
@overload
def dict_match(dict_match:dict[int,Callable[[Any],bool]], value:Any) -> int: ...
def dict_match(dict_match:dict[Any,Callable[[Any],bool]], value:Any) -> Any:
    for key, cond in dict_match.items():
        if cond(value): return key
    raise DictMatchException