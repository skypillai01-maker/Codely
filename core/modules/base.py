from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseModule(ABC):
    """Abstract base class for all pluggable modules."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the module."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of what the module does."""
        pass

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """The main execution logic for the module."""
        pass
