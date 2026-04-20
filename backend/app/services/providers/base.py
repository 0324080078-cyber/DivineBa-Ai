from abc import ABC, abstractmethod
from typing import List, Dict


class LLMProvider(ABC):
    """
    Abstract base class for all LLM provider plug-ins.

    To add a new provider (e.g. Grok, Deepseek):
        1. Create a file in app/services/providers/<name>_provider.py
        2. Subclass LLMProvider and implement both methods.
        3. Register it in app/services/provider_factory.py.
    """

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], model: str) -> str:
        """Send a list of chat messages and return the assistant reply."""
        ...

    @abstractmethod
    async def embed(self, texts: List[str], model: str) -> List[List[float]]:
        """Return embedding vectors for each text."""
        ...
