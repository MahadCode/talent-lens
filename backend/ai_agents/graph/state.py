"""Shared, strongly typed state passed between LangGraph nodes.

`HiringState` is intentionally a `TypedDict` (rather than a Pydantic
model) because LangGraph's `StateGraph` natively merges partial updates
into a `TypedDict` state via reducers; using a plain dict-like type keeps
node return values simple (`{"field": value}`) while `total=False` makes
every field optional so nodes can be added incrementally.
"""

from __future__ import annotations

from typing import Any, TypedDict

from ai_agents.utils.schemas import (
    DecisionResult,
    EmailContent,
    GithubEvaluationResult,
    InterviewResult,
    MatchingResult,
    ParsedCandidate,
    ScoringResult,
)


class HiringState(TypedDict, total=False):
    """End-to-end state threaded through the hiring LangGraph workflow.

    Every field is optional (`total=False`) so the graph can be extended
    with new nodes/fields without breaking existing state constructions.

    Attributes:
        job_description: Free-text job description supplied by the caller.
        job_requirements: Free-text or structured job requirements.
        resume_text: Raw resume text to be parsed.
        parsed_candidate: Structured candidate data extracted from the resume.
        matching_result: Result of comparing candidate to job requirements.
        score_result: Result of the candidate scoring agent.
        decision: Result of the decision agent.
        email_content: Generated email content for the candidate.
        interview_questions: Adaptive interview questions generated so far.
        interview_result: Aggregate result of the interview process.
        github_result: Result of the GitHub evaluation agent.
        final_recommendation: Final hiring recommendation narrative.
        extra: Free-form bucket for future agents to stash additional data
            without requiring a schema change to this `TypedDict`.
    """

    job_description: str
    job_requirements: str
    resume_text: str
    parsed_candidate: ParsedCandidate
    matching_result: MatchingResult
    score_result: ScoringResult
    decision: DecisionResult
    email_content: EmailContent
    interview_questions: list[str]
    interview_result: InterviewResult
    github_result: GithubEvaluationResult
    final_recommendation: str
    extra: dict[str, Any]
