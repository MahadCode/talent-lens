"""Candidate Scoring Agent.

Produces per-dimension and total scores for a candidate, delegating all
LLM interaction to `scoring_chain`.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from ai_agents.chains.scoring_chain import score_candidate
from ai_agents.utils.schemas import MatchingResult, ParsedCandidate, ScoringResult


class CandidateScoringAgent:
    """Computes weighted scores for a candidate across multiple dimensions."""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the agent.

        Args:
            llm: Optional chat model override, primarily for testing.
        """

        self._llm = llm

    def run(self, parsed_candidate: ParsedCandidate, matching_result: MatchingResult) -> ScoringResult:
        """Score a candidate.

        Args:
            parsed_candidate: The candidate's structured profile.
            matching_result: Output of the skill-matching agent.

        Returns:
            A validated `ScoringResult` instance with a 0-100 total score.
        """

        return score_candidate(
            parsed_candidate=parsed_candidate,
            matching_result=matching_result,
            llm=self._llm,
        )
