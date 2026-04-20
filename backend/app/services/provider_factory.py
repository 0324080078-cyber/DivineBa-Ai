"""
Provider plug-in factory.

To add Grok or Deepseek later:
  1. Create app/services/providers/grok_provider.py (subclass LLMProvider)
  2. Add an elif branch below referencing the new class.
  3. Set CYRUS_PROVIDER=grok in .env.
"""

from app.core.config import settings
from app.services.providers.base import LLMProvider


def get_provider() -> LLMProvider:
    if settings.CYRUS_PROVIDER == "openai":
        from app.services.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()

    # ── Future providers ──────────────────────────────────────────────────
    # elif settings.CYRUS_PROVIDER == "grok":
    #     from app.services.providers.grok_provider import GrokProvider
    #     return GrokProvider()
    #
    # elif settings.CYRUS_PROVIDER == "deepseek":
    #     from app.services.providers.deepseek_provider import DeepseekProvider
    #     return DeepseekProvider()
    # ─────────────────────────────────────────────────────────────────────

    raise ValueError(
        f"Unknown CYRUS_PROVIDER: '{settings.CYRUS_PROVIDER}'. "
        "Supported: openai  (grok/deepseek coming soon)"
    )
