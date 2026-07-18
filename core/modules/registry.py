import importlib
import os
from typing import Dict, Type
from core.modules.base import BaseModule

class ModuleRegistry:
    _instance = None
    _modules: Dict[str, BaseModule] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModuleRegistry, cls).__new__(cls)
        return cls._instance

    def register(self, module: BaseModule):
        self._modules[module.name] = module

    def get_module(self, name: str) -> BaseModule:
        return self._modules.get(name)

    def list_modules(self):
        return [
            {"name": m.name, "description": m.description}
            for m in self._modules.values()
        ]

    def discover_modules(self, modules_path: str = "modules"):
        """Dynamically load modules from the modules/ directory."""
        if not os.path.exists(modules_path):
            os.makedirs(modules_path, exist_ok=True)
            return

        for folder in os.listdir(modules_path):
            module_dir = os.path.join(modules_path, folder)
            if os.path.isdir(module_dir) and os.path.exists(os.path.join(module_dir, "__init__.py")):
                try:
                    # Dynamically import the module
                    importlib.import_module(f"modules.{folder}")
                except Exception as e:
                    print(f"Failed to load module {folder}: {e}")

# Global registry instance
registry = ModuleRegistry()
