"""
Model factory and configuration for AuditPilot agents.
Supports Google Gemini, Groq (Llama 3), and other providers via Google ADK and LiteLLM.
"""

import os
from google.adk.models.base_llm import BaseLlm
from google.adk.models.google_llm import Gemini
from google.adk.models.registry import LLMRegistry
from google.genai.types import HttpRetryOptions


def get_model(model_name: str | None = None) -> BaseLlm:
    """Configures and returns an LLM model instance for AuditPilot agents.

    Supports:
    - Google Gemini: 'gemini-3.8-flash', 'gemini-2.5-flash', etc. (default)
    - Groq via LiteLLM: 'groq/llama-3.3-70b-versatile', 'groq/llama-3.1-8b-instant', etc.
    - Other providers via LiteLLM: 'openai/...', 'claude-...', etc.

    Resolution order:
    1. Explicit `model_name` passed to function.
    2. Environment variable `LLM_MODEL`.
    3. Environment variable `GEMINI_MODEL`.
    4. Auto-detection: If `GROQ_API_KEY` is present and no Gemini/Google key is set,
       defaults to 'groq/llama-3.3-70b-versatile'.
    5. Default fallback: 'gemini-3.8-flash'.

    Args:
        model_name: Optional override model identifier.

    Returns:
        Configured BaseLlm model instance.
    """
    name = model_name or os.getenv("LLM_MODEL") or os.getenv("GEMINI_MODEL")

    if not name:
        if os.getenv("GROQ_API_KEY") and not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            name = "groq/llama-3.3-70b-versatile"
        else:
            name = "gemini-3.8-flash"

    # Prepend groq/ if user provided bare llama model identifier
    if name.startswith("llama-"):
        name = f"groq/{name}"

    # Non-Gemini model (Groq, OpenAI, Anthropic, Ollama, etc.) -> resolve via ADK registry
    if name.startswith("groq/") or "/" in name or name.startswith("claude-") or name.startswith("gpt-"):
        return LLMRegistry.new_llm(name)

    # Standard Gemini with exponential backoff on transient 503 / 429 errors
    retry_options = HttpRetryOptions(
        attempts=5,
        initial_delay=2.0,
        max_delay=12.0,
        exp_base=2.0,
        jitter=1.0,
        http_status_codes=[408, 429, 500, 502, 503, 504],
    )
    return Gemini(model=name, retry_options=retry_options)


# Alias for backward compatibility with existing agent imports
get_gemini_model = get_model
