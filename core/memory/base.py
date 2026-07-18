from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseMemory(ABC):
    """Abstract base class for context-isolated memory."""
    
    @abstractmethod
    def add(self, context_id: str, text: str, metadata: Dict[str, Any] = None):
        """Add text and metadata to a specific context's memory."""
        pass

    @abstractmethod
    def search(self, context_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant context within a specific context ID."""
        pass

    @abstractmethod
    def clear(self, context_id: str):
        """Clear all memory for a specific context ID."""
        pass
