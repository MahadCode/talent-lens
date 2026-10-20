"""Skill Matching Agent.

Compares a parsed candidate profile against job requirements and produces
a structured match assessment, delegating all LLM interaction to
`matcher_chain`.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from ai_agents.chains.matcher_chain import match_candidate
from ai_agents.utils.schemas import MatchingResult, ParsedCandidate


class SkillMatchingAgent:
    """Assesses how well a candidate matches a job's requirements."""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the agent.

        Args:
            llm: Optional chat model override, primarily for testing.
        """

        self._llm = llm

    def run(self, job_requirements: str, parsed_candidate: ParsedCandidate) -> MatchingResult:
        """Assess candidate-to-job fit.

        Args:
            job_requirements: Free-text description of job requirements.
            parsed_candidate: The candidate's structured profile.

        Returns:
            A validated `MatchingResult` instance.

        Raises:
            ValueError: If `job_requirements` is empty or whitespace-only.
        """

        if not job_requirements or not job_requirements.strip():
            raise ValueError("job_requirements must be a non-empty string.")

        return match_candidate(
            job_requirements=job_requirements,
            parsed_candidate=parsed_candidate,
            llm=self._llm,
        )
