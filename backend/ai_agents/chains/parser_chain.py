"""Chain that turns raw resume text into a `ParsedCandidate`.

The chain is a plain LCEL pipeline (`prompt | llm`) so it can be reused
directly inside a LangGraph node or invoked standalone/in tests without
any LangGraph dependency.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable

from ai_agents.config.llm import get_gemini_llm
from ai_agents.prompts.parser_prompt import parser_prompt
from ai_agents.utils.schemas import ParsedCandidate


def build_parser_chain(llm: BaseChatModel | None = None) -> Runnable[dict, ParsedCandidate]:
    """Build the resume parsing chain.

    Args:
        llm: Optional chat model override, primarily for testing. Defaults
            to the shared Gemini client.

    Returns:
        A runnable that accepts `{"resume_text": str}` and returns a
        validated `ParsedCandidate`.
    """

    model = llm or get_gemini_llm()
    structured_model = model.with_structured_output(ParsedCandidate)
    return parser_prompt | structured_model


def parse_resume(resume_text: str, llm: BaseChatModel | None = None) -> ParsedCandidate:
    """Parse raw resume text into a structured candidate profile.

    Args:
        resume_text: The raw text content of the candidate's resume.
        llm: Optional chat model override, primarily for testing.

    Returns:
        A validated `ParsedCandidate` instance.
    """

    chain = build_parser_chain(llm=llm)
    result = chain.invoke({"resume_text": resume_text})
    return result
