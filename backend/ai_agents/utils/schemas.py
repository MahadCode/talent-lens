"""Pydantic v2 schemas shared across agents, chains, and graph nodes.

Keeping these in a single `utils` module avoids duplicate schema
definitions between a chain's output parser and the node that consumes
that output.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ParsedCandidate(BaseModel):
    """Structured information extracted from a candidate's resume."""

    name: str | None = Field(default=None, description="Candidate full name.")
    email: str | None = Field(default=None, description="Candidate email address.")
    phone: str | None = Field(default=None, description="Candidate phone number.")
    skills: list[str] = Field(default_factory=list, description="Technical and soft skills.")
    experience: list[str] = Field(
        default_factory=list,
        description="Work experience entries, each summarized as one string.",
    )
    education: list[str] = Field(default_factory=list, description="Education entries.")
    projects: list[str] = Field(default_factory=list, description="Notable projects.")
    certifications: list[str] = Field(default_factory=list, description="Certifications held.")
    github: str | None = Field(default=None, description="GitHub profile URL, if present.")
    linkedin: str | None = Field(default=None, description="LinkedIn profile URL, if present.")


class MatchingResult(BaseModel):
    """Result of comparing a parsed candidate against job requirements."""

    match_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall skill match percentage.")
    missing_skills: list[str] = Field(default_factory=list, description="Required skills the candidate lacks.")
    extra_skills: list[str] = Field(
        default_factory=list, description="Candidate skills not required by the job."
    )
    experience_comparison: str = Field(
        ..., description="Narrative comparison of candidate experience vs. job requirements."
    )
    explanation: str = Field(..., description="Overall rationale for the match assessment.")


class ScoreBreakdown(BaseModel):
    """Individual scoring dimensions, each on a 0-100 scale."""

    skills_score: float = Field(..., ge=0.0, le=100.0)
    experience_score: float = Field(..., ge=0.0, le=100.0)
    projects_score: float = Field(..., ge=0.0, le=100.0)
    education_score: float = Field(..., ge=0.0, le=100.0)
    certifications_score: float = Field(..., ge=0.0, le=100.0)


class ScoringResult(BaseModel):
    """Complete output of the candidate scoring agent."""

    breakdown: ScoreBreakdown = Field(..., description="Per-dimension scores.")
    total_score: float = Field(..., ge=0.0, le=100.0, description="Weighted total score, 0-100.")
    reasoning: str = Field(..., description="Explanation of how the total score was derived.")


class DecisionType(str, Enum):
    """Possible outcomes of the hiring decision agent."""

    SHORTLIST = "SHORTLIST"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECT = "REJECT"


class DecisionResult(BaseModel):
    """Output of the decision agent."""

    decision: DecisionType = Field(..., description="Final routing decision for the candidate.")
    reason: str = Field(..., description="Explanation for why this decision was reached.")


class EmailType(str, Enum):
    """Supported categories of candidate-facing emails."""

    SHORTLIST = "SHORTLIST"
    REJECTION = "REJECTION"
    INTERVIEW_INVITATION = "INTERVIEW_INVITATION"


class EmailContent(BaseModel):
    """Generated email content. This agent never sends email; it only drafts it."""

    subject: str = Field(..., description="Email subject line.")
    body: str = Field(..., description="Full email body text.")


class InterviewQuestion(BaseModel):
    """A single adaptive interview question."""

    question: str = Field(..., description="The interview question text.")
    focus_area: str = Field(..., description="Skill or weakness this question targets.")
    is_follow_up: bool = Field(default=False, description="Whether this is a follow-up to a prior answer.")


class InterviewResult(BaseModel):
    """Aggregate result of an interview session."""

    questions_asked: list[InterviewQuestion] = Field(default_factory=list)
    overall_assessment: str = Field(..., description="Summary assessment of the candidate's interview performance.")
    passed: bool = Field(..., description="Whether the candidate passed the interview.")


class GithubEvaluationResult(BaseModel):
    """Output of the GitHub evaluation agent."""

    score: float = Field(..., ge=0.0, le=100.0, description="Overall GitHub quality score.")
    repository_quality: str = Field(..., description="Assessment of repository quality.")
    languages_used: list[str] = Field(default_factory=list, description="Primary languages observed.")
    commit_consistency: str = Field(..., description="Assessment of commit frequency/consistency.")
    ai_ml_projects_present: bool = Field(..., description="Whether AI/ML projects were found.")
    documentation_quality: str = Field(..., description="Assessment of README/documentation quality.")
    code_quality: str = Field(..., description="Assessment of overall code quality.")
    explanation: str = Field(..., description="Overall rationale for the score.")
