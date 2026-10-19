"""Chain that compares a parsed candidate against job requirements."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable

from ai_agents.config.llm import get_gemini_llm
from ai_agents.prompts.matcher_prompt import matcher_prompt
from ai_agents.utils.schemas import MatchingResult, ParsedCandidate


def build_matcher_chain(llm: BaseChatModel | None = None) -> Runnable[dict, MatchingResult]:
    """Build the skill-matching chain.

    Args:
        llm: Optional chat model override, primarily for testing.

    Returns:
        A runnable accepting `{"job_requirements": str, "parsed_candidate_json": str}`
        and returning a validated `MatchingResult`.
    """

    model = llm or get_gemini_llm()
    structured_model = model.with_structured_output(MatchingResult)
    return matcher_prompt | structured_model


def match_candidate(
    job_requirements: str,
    parsed_candidate: ParsedCandidate,
    llm: BaseChatModel | None = None,
) -> MatchingResult:
    """Compare a parsed candidate against job requirements.

    Args:
        job_requirements: Free-text description of job requirements.
        parsed_candidate: The candidate's structured profile.
        llm: Optional chat model override, primarily for testing.

    Returns:
        A validated `MatchingResult` instance.
    """

    chain = build_matcher_chain(llm=llm)
    return chain.invoke(
        {
            "job_requirements": job_requirements,
            "parsed_candidate_json": parsed_candidate.model_dump_json(),
        }
    )
