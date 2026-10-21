"""Chain that scores a candidate across multiple weighted dimensions."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable

from ai_agents.config.llm import get_gemini_llm
from ai_agents.prompts.scoring_prompt import scoring_prompt
from ai_agents.utils.schemas import MatchingResult, ParsedCandidate, ScoringResult


def build_scoring_chain(llm: BaseChatModel | None = None) -> Runnable[dict, ScoringResult]:
    """Build the candidate scoring chain.

    Args:
        llm: Optional chat model override, primarily for testing.

    Returns:
        A runnable accepting `{"parsed_candidate_json": str, "matching_result_json": str}`
        and returning a validated `ScoringResult`.
    """

    model = llm or get_gemini_llm()
    structured_model = model.with_structured_output(ScoringResult)
    return scoring_prompt | structured_model


def score_candidate(
    parsed_candidate: ParsedCandidate,
    matching_result: MatchingResult,
    llm: BaseChatModel | None = None,
) -> ScoringResult:
    """Score a candidate given their profile and skill-matching assessment.

    Args:
        parsed_candidate: The candidate's structured profile.
        matching_result: The output of the skill-matching chain.
        llm: Optional chat model override, primarily for testing.

    Returns:
        A validated `ScoringResult` instance.
    """

    chain = build_scoring_chain(llm=llm)
    return chain.invoke(
        {
            "parsed_candidate_json": parsed_candidate.model_dump_json(),
            "matching_result_json": matching_result.model_dump_json(),
        }
    )
