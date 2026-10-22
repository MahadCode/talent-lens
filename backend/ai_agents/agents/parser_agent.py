"""Resume Parser Agent.

Responsible for turning raw resume text into a validated, structured
candidate profile. All LLM interaction is delegated to `parser_chain`; this
agent's job is to expose a stable, dependency-injected interface that the
LangGraph node layer can call.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from ai_agents.chains.parser_chain import parse_resume
from ai_agents.utils.schemas import ParsedCandidate


class ResumeParserAgent:
    """Extracts structured candidate information from raw resume text."""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the agent.

        Args:
            llm: Optional chat model override, primarily for testing.
                Defaults to the shared Gemini client when not provided.
        """

        self._llm = llm

    def run(self, resume_text: str) -> ParsedCandidate:
        """Parse a candidate's resume.

        Args:
            resume_text: Raw resume text to extract information from.

        Returns:
            A validated `ParsedCandidate` describing the candidate.

        Raises:
            ValueError: If `resume_text` is empty or whitespace-only.
        """

        if not resume_text or not resume_text.strip():
            raise ValueError("resume_text must be a non-empty string.")

        return parse_resume(resume_text=resume_text, llm=self._llm)
