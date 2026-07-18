import requests
import json
import base64
import logging
import time
from typing import List, Dict, Any, Generator, Optional
from core.llm.base import BaseLLM
from core.config import CHAT_MODEL, OLLAMA_BASE_URL, CHAT_TIMEOUT, EMBED_TIMEOUT

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 2  # Exponential backoff multiplier


class OllamaAdapter(BaseLLM):
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or OLLAMA_BASE_URL
        self.model = model or CHAT_MODEL
        self.chat_timeout = CHAT_TIMEOUT
        self.embed_timeout = EMBED_TIMEOUT

    def generate(self, prompt: str, context: List[Dict[str, str]] = None, session_id: str = None) -> str:
        """
        Generate a response using the /api/chat endpoint for session isolation.
        
        Each session_id creates an isolated conversation context in Ollama,
        preventing cross-thread contamination.
        """
        url = f"{self.base_url}/api/chat"
        
        messages = []
        
        # Build message history from context if provided
        if context:
            for ctx in context:
                role = ctx.get("role", "user")
                content = ctx.get("content", "")
                messages.append({"role": role, "content": content})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        # Add session_id for conversation isolation if provided
        if session_id:
            payload["session_id"] = session_id
            logger.debug(f"Using session_id: {session_id}")
        
        try:
            logger.info(f"Generating response for prompt length: {len(prompt)}")
            response = self._request_with_retry(url, payload, self.chat_timeout)
            result = response.json()
             
            # Extract response content
            response_text = result.get("message", {}).get("content", "")
            logger.info(f"Response generated, length: {len(response_text)}")
             
            return response_text
             
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection failed to Ollama at {self.base_url}: {e}")
            raise RuntimeError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Ensure Ollama is installed and running. "
                "Download from: https://ollama.com/download"
            )
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout to Ollama: {e}")
            raise RuntimeError(f"Request to Ollama timed out: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Ollama failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"Request to Ollama failed: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Ollama: {e}")
            raise RuntimeError(f"Invalid response from Ollama: {e}")

    def stream(self, prompt: str, context: List[Dict[str, str]] = None, session_id: str = None) -> Generator[str, None, None]:
        """
        Stream response chunks using /api/chat for session isolation.
        """
        url = f"{self.base_url}/api/chat"
        
        messages = []
        if context:
            for ctx in context:
                role = ctx.get("role", "user")
                content = ctx.get("content", "")
                messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        try:
            with requests.post(url, json=payload, stream=True, timeout=self.chat_timeout) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection failed during streaming: {e}")
            raise RuntimeError(f"Could not connect to Ollama at {self.base_url}.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Streaming request failed: {type(e).__name__}: {e}")
            raise RuntimeError(f"Streaming request failed: {e}")

    def embed(self, text: str) -> List[float]:
        """Generate embeddings for a given text."""
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }
        try:
            response = self._request_with_retry(url, payload, self.embed_timeout)
            response.raise_for_status()
            embedding = response.json().get("embedding", [])
            if not embedding:
                logger.warning(f"Empty embedding returned for text length={len(text)}")
            return embedding
        except requests.exceptions.Timeout as e:
            logger.error(f"Embedding request timeout: {e}")
            raise RuntimeError(f"Embedding request timed out for model '{self.model}'.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Embedding failed for model '{self.model}': {type(e).__name__}: {e}")
            raise RuntimeError(
                f"Embedding not available for model '{self.model}'. "
                "Use a dedicated embedding model like nomic-embed-text."
            )
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in embedding response: {e}")
            raise RuntimeError(f"Invalid embedding response for model '{self.model}'.")

    def validate_connectivity(self) -> bool:
        """Verify that the Ollama server is running and reachable."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"Ollama connection validated at {self.base_url}")
                return True
            logger.warning(f"Ollama returned status {response.status_code}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama connectivity check failed: {type(e).__name__}: {e}")
            return False

    def list_models(self) -> List[str]:
        """List all available models on the Ollama server."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                logger.info(f"Found {len(models)} models on Ollama")
                return models
            logger.warning(f"Failed to list models, status: {response.status_code}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list models: {type(e).__name__}: {e}")
            return []

    def describe_image(self, image_path: str, prompt: str = "Describe this image in detail.") -> str:
        """Use Ollama's vision capabilities (e.g., with llava or moondream)."""
        url = f"{self.base_url}/api/chat"
        
        messages = [
            {"role": "user", "content": prompt, "images": [self._encode_image(image_path)]}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = self._request_with_retry(url, payload, self.chat_timeout)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "Image description unavailable")
        except requests.exceptions.RequestException as e:
            logger.error(f"Image description failed: {type(e).__name__}: {e}")
            return f"Image description failed: {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in image description response: {e}")
            return "Image description failed: Invalid response"

    def _request_with_retry(self, url: str, payload: dict, timeout: int) -> requests.Response:
        """Make HTTP request with retry logic.
        
        Connection errors fail immediately. Transient errors (timeouts) retry
        up to MAX_RETRIES times with exponential backoff.
        """
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(url, json=payload, timeout=timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection failed to Ollama at {self.base_url}")
                raise RuntimeError(
                    f"Could not connect to Ollama at {self.base_url}. "
                    "Ensure Ollama is installed and running."
                )
            except requests.exceptions.Timeout as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_BACKOFF ** attempt
                    logger.warning(f"Request timed out (attempt {attempt + 1}/{MAX_RETRIES}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
            except requests.exceptions.RequestException as e:
                logger.error(f"Request to Ollama failed: {type(e).__name__}: {e}")
                raise RuntimeError(f"Request to Ollama failed: {e}")
        logger.error(f"Request failed after {MAX_RETRIES} attempts: {last_error}")
        raise RuntimeError(str(last_error))

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
