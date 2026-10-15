"""LLM extraction of structured requirements from a free-text job description."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ai_agents.config.llm import get_gemini_llm


class ExtractedRequirements(BaseModel):
    """Structured requirements pulled from a job posting."""

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience: str = ""
    qualifications: list[str] = Field(default_factory=list)


_SYSTEM_PROMPT = """You extract hiring requirements from a job description.
Return only structured data. Do not invent skills that the text does not support.
Split required skills from preferred skills. Put years or seniority in experience.
Put degrees and certifications in qualifications.
"""


def extract_requirements(description: str, requirements: str) -> dict:
    """Ask the shared LLM to structure a job's free-text requirements.

    Args:
        description: The job description.
        requirements: The free-text requirements field.

    Returns:
        A dict matching `ExtractedRequirements`.
    """

    llm = get_gemini_llm()
    structured_llm = llm.with_structured_output(ExtractedRequirements)
    result = structured_llm.invoke(
        [
            ("system", _SYSTEM_PROMPT),
            (
                "human",
                f"Job description:\n{description}\n\nRequirements:\n{requirements}",
            ),
        ]
    )
    return result.model_dump()
