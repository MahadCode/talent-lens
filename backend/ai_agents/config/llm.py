"""Factory for the shared Gemini chat model used across all agents.

Centralizing LLM construction here means every agent/chain depends on a
single, testable factory function rather than instantiating
`ChatGoogleGenerativeAI` ad hoc, which would scatter API-key handling and
model configuration throughout the codebase.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from ai_agents.config.settings import get_settings


@lru_cache(maxsize=1)
def get_gemini_llm() -> ChatGoogleGenerativeAI:
    """Build (and cache) the shared Gemini 2.5 Flash chat model.

    The instance is cached because `ChatGoogleGenerativeAI` objects are
    stateless with respect to conversation history (state is passed in via
    messages at call time), so a single shared client can safely be reused
    by every agent/chain in the process.

    Returns:
        A configured `ChatGoogleGenerativeAI` client ready for use in
        LangChain chains and LangGraph nodes.
    """

    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        temperature=settings.llm_temperature,
        google_api_key=settings.google_api_key,
    )
