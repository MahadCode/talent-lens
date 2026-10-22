"""Interview Agent.

Generates adaptive interview questions one at a time, supporting follow-up
questions that probe deeper into a candidate's prior answer.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from ai_agents.chains.interview_chain import generate_next_question
from ai_agents.utils.schemas import InterviewQuestion


class InterviewAgent:
    """Produces one adaptive interview question at a time."""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the agent.

        Args:
            llm: Optional chat model override, primarily for testing.
        """

        self._llm = llm

    def next_question(
        self,
        job_description: str,
        candidate_skills: list[str],
        candidate_weaknesses: list[str],
        conversation_history: list[str] | None = None,
    ) -> InterviewQuestion:
        """Generate the next interview question, optionally a follow-up.

        Args:
            job_description: Free-text job description.
            candidate_skills: Skills demonstrated by the candidate.
            candidate_weaknesses: Missing or weak skills identified earlier.
            conversation_history: Prior Q&A pairs, formatted as strings,
                oldest first. Pass the candidate's most recent answer as
                the last entry to allow the agent to generate a follow-up.

        Returns:
            The next `InterviewQuestion` to pose to the candidate.
        """

        return generate_next_question(
            job_description=job_description,
            candidate_skills=candidate_skills,
            candidate_weaknesses=candidate_weaknesses,
            conversation_history=conversation_history,
            llm=self._llm,
        )
