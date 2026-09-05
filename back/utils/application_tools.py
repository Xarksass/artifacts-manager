import importlib
import pkgutil
from types import ModuleType

from fastapi import APIRouter, FastAPI


def load_routers(app: FastAPI, controller_module: ModuleType):
    """
    Load every routers within the module
    """
    prefix = f"{controller_module.__name__}."
    for _, module_name, _ in pkgutil.walk_packages(controller_module.__path__, prefix):
        module = importlib.import_module(module_name)
        for obj in vars(module).values():
            if isinstance(obj, APIRouter):
                app.include_router(obj)