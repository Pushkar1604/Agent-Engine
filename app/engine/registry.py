from typing import Callable, Dict, Any, Awaitable

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {}

    def register(self, name: str, fn):
        if not callable(fn):
            raise ValueError("fn must be callable")
        self._tools[name] = fn

    def get(self, name: str):
        return self._tools.get(name)

    def list(self):
        return list(self._tools.keys())

# module-level registry
registry = ToolRegistry()
