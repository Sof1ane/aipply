import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LLMClient:
    """Simple pluggable LLM client supporting either Anthropic Claude API or local Ollama (e.g., Mistral)."""

    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError

    @staticmethod
    def from_config(
        backend: str,
        model: str,
        ollama_url: str = "http://localhost:11434",
        anthropic_key: Optional[str] = None,
        extra_options: Optional[Dict[str, Any]] = None,
    ) -> "LLMClient":
        backend_lower = (backend or "").strip().lower()
        if backend_lower in ("ollama", "mistral", "local"):
            return OllamaClient(model=model, base_url=ollama_url, options=extra_options or {})
        if backend_lower in ("claude", "anthropic"):
            api_key = anthropic_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY or pass --anthropic-key.")
            return ClaudeClient(model=model or "claude-3-5-sonnet-latest", api_key=api_key)
        raise ValueError(f"Unsupported backend: {backend}")


class OllamaClient(LLMClient):
    def __init__(self, model: str, base_url: str = "http://localhost:11434", options: Optional[Dict[str, Any]] = None) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.options = options or {"temperature": 0.3}

    def generate(self, prompt: str, **kwargs) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {**self.options, **kwargs.get("options", {})},
        }
        response = requests.post(url, json=payload, timeout=kwargs.get("timeout", 120))
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()


class ClaudeClient(LLMClient):
    def __init__(self, model: str, api_key: str) -> None:
        self.model = model
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"

    def generate(self, prompt: str, **kwargs) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2024-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 1200),
            "temperature": kwargs.get("temperature", 0.3),
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=kwargs.get("timeout", 120))
        response.raise_for_status()
        data = response.json()
        # Claude returns content as a list of blocks; extract text
        content = data.get("content", [])
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif isinstance(block, str):
                text_parts.append(block)
        return "\n".join([p for p in text_parts if p]).strip()


