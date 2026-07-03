"""API v2 package compatibility helpers."""

import importlib
import sys
from types import ModuleType


def __getattr__(name: str) -> ModuleType:
    if name != "chat":
        raise AttributeError(name)

    module = importlib.import_module("app.api.bijmantra.ai.chat")
    sys.modules[f"{__name__}.chat"] = module
    globals()[name] = module
    return module
