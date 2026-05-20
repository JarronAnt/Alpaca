# src/alpaca/core/llm.py
"""LLM client with retry logic and error handling."""

from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from alpaca.config import Config
from alpaca.exceptions import LLMError
from alpaca.logger import get_logger
from alpaca.models import Message

logger = get_logger(__name__)


class LLMClient:
    """Client for LLM API calls with retry logic."""
    
    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ):
        self.base_url = base_url or Config.ollama_url
        self.timeout = timeout or Config.llm_timeout
        self.max_retries = max_retries or Config.llm_max_retries
        
    def _prepare_messages(self, messages: list[Message] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert messages to Ollama format - handles both Message objects and raw dicts."""
        ollama_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                # Raw dict from working version
                ollama_msg = {
                    "role": msg.get("role"),
                    "content": msg.get("content", ""),
                }
                if msg.get("name"):
                    ollama_msg["name"] = msg["name"]
            else:
                # Pydantic Message model
                role = msg.role.value
                if role == "tool":
                    role = "assistant"
                ollama_msg = {
                    "role": role,
                    "content": msg.content,
                }
                if msg.name:
                    ollama_msg["name"] = msg.name
            
            ollama_messages.append(ollama_msg)
        
        return ollama_messages
        
    @retry(
        retry=retry_if_exception_type((requests.RequestException, LLMError)),
        stop=stop_after_attempt(Config.llm_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def chat(
        self,
        model: str,
        messages: list[Message] | list[dict[str, Any]],  # Accept both types
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str:
        """Send a chat completion request with retry logic."""
        
        ollama_messages = self._prepare_messages(messages)
        
        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        
        try:
            logger.debug(
                "Sending LLM request",
                model=model,
                message_count=len(ollama_messages),
            )
            
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            
            # Log raw response for debugging
            logger.debug(
                "Raw response received",
                status_code=response.status_code,
                content_preview=response.text[:200] if response.text else "empty",
            )
            
            response.raise_for_status()
            
            try:
                data = response.json()
            except Exception as e:
                logger.error("Failed to parse JSON response", text=response.text[:500])
                raise LLMError(f"Invalid JSON response: {e}")
            
            # Extract content from various possible response formats
            content = ""
            
            if isinstance(data, dict):
                # Standard Ollama chat format
                if "message" in data and isinstance(data["message"], dict):
                    content = data["message"].get("content", "")
                # Ollama generate format (fallback)
                elif "response" in data:
                    content = data["response"]
                # Direct content field
                elif "content" in data:
                    content = data["content"]
                else:
                    logger.error("Unknown response structure", keys=list(data.keys()))
                    raise LLMError(f"Unknown response format. Keys: {list(data.keys())}")
            else:
                content = str(data)
            
            if not content or not content.strip():
                logger.error(
                    "Empty content from LLM",
                    model=model,
                    response_data=data,
                )
                raise LLMError(f"Empty response from model '{model}'")
            
            logger.debug(
                "LLM response processed",
                model=model,
                content_length=len(content),
            )
            
            return content.strip()
            
        except requests.Timeout:
            logger.error("LLM request timed out", model=model, timeout=self.timeout)
            raise LLMError(f"Request timed out after {self.timeout}s")
        except requests.RequestException as e:
            logger.error("LLM request failed", model=model, error=str(e))
            raise LLMError(f"Request failed: {e}")
        except LLMError:
            raise
        except Exception as e:
            logger.error("Unexpected LLM error", model=model, error=str(e))
            raise LLMError(f"Unexpected error: {e}")
    
    def health_check(self) -> bool:
        """Check if Ollama is available."""
        try:
            # Try to list models as health check
            base = self.base_url.replace("/api/chat", "/api/tags")
            response = requests.get(base, timeout=5)
            return response.status_code == 200
        except Exception:
            return False


# Global client instance
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def call_llm(
    model: str,
    messages: list[Message] | list[dict[str, Any]],  # Accept both types
    temperature: float = 0.7,
) -> str:
    """Convenience function for LLM calls."""
    client = get_llm_client()
    return client.chat(model, messages, temperature)
