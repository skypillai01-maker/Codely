from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator

class BaseLLM(ABC):
    """Abstract base class for LLM adapters."""
    
    @abstractmethod
    def generate(self, prompt: str, context: List[Dict[str, str]] = None) -> str:
        """Generate a complete response from a prompt."""
        pass

    @abstractmethod
    def stream(self, prompt: str, context: List[Dict[str, str]] = None) -> Generator[str, None, None]:
        """Stream response chunks from a prompt."""
        pass

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embeddings for a given text."""
        pass

    @abstractmethod
    def validate_connectivity(self) -> bool:
        """Check if the LLM provider is reachable and correctly configured."""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """List all available models on the runtime."""
        pass

    @abstractmethod
    def describe_image(self, image_path: str, prompt: str = "Describe this image in detail.") -> str:
        """Use a vision-capable model to describe an image."""
        pass
