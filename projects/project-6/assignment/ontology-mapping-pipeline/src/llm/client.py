"""
LLM Client Module

Provides a unified interface for interacting with different LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
import asyncio
import os

from pydantic import BaseModel
import yaml


@dataclass
class LLMResponse:
    """Represents a response from an LLM."""
    content: str
    model: str
    usage: dict[str, int]
    raw_response: Any = None


class LLMClient(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: dict):
        self.config = config
        self.model = config.get("model")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.1)
        self.timeout = config.get("timeout", 60)
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Send a completion request to the LLM."""
        pass
    
    @abstractmethod
    async def complete_with_system(
        self, system: str, user: str, **kwargs
    ) -> LLMResponse:
        """Send a completion with separate system and user messages."""
        pass


class ClaudeClient(LLMClient):
    """Anthropic Claude implementation."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
        
        api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in config or environment")
        
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Send a completion request to Claude."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            messages=[{"role": "user", "content": prompt}],
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            raw_response=response,
        )
    
    async def complete_with_system(
        self, system: str, user: str, **kwargs
    ) -> LLMResponse:
        """Send a completion with separate system and user messages."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            raw_response=response,
        )


class OpenAIClient(LLMClient):
    """OpenAI GPT implementation."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        
        api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in config or environment")
        
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Send a completion request to OpenAI."""
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            messages=[{"role": "user", "content": prompt}],
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
            raw_response=response,
        )
    
    async def complete_with_system(
        self, system: str, user: str, **kwargs
    ) -> LLMResponse:
        """Send a completion with separate system and user messages."""
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
            raw_response=response,
        )


def create_llm_client(config_path: str = "configs/llm_config.yaml") -> LLMClient:
    """Factory function to create an LLM client from configuration."""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    provider = config.get("provider", "anthropic")
    provider_config = config.get(provider, {})
    
    # Expand environment variables in config
    for key, value in provider_config.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            provider_config[key] = os.environ.get(env_var)
    
    if provider == "anthropic":
        return ClaudeClient(provider_config)
    elif provider == "openai":
        return OpenAIClient(provider_config)
    else:
        raise ValueError(f"Unknown provider: {provider}")
