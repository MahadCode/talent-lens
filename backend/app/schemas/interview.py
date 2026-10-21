"""Pydantic schemas for interview endpoints."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class InterviewQuestionRequest(BaseModel):
    """Request body for `POST /interview/questions`."""

    candidate_id: uuid.UUID = Field(..., description="Candidate to generate a question for.")
    job_description: str = Field(..., min_length=1, description="Job description to ground the question in.")
    conversation_history: list[str] = Field(
        default_factory=list,
        description="Prior Q&A turns, oldest first, used to generate an adaptive follow-up.",
    )


class InterviewQuestionResponse(BaseModel):
    """Response body for `POST /interview/questions`."""

    question: str
    focus_area: str
    is_follow_up: bool


class InterviewEvaluateRequest(BaseModel):
    """Request body for `POST /interview/evaluate`."""

    candidate_id: uuid.UUID = Field(..., description="Candidate whose interview is being evaluated.")
    questions_and_answers: list[str] = Field(
        ..., min_length=1, description="Full Q&A transcript, formatted as strings."
    )


class InterviewEvaluateResponse(BaseModel):
    """Response body for `POST /interview/evaluate`."""

    interview_id: uuid.UUID
    overall_assessment: str
    passed: bool


class StoredQuestionRead(BaseModel):
    """One saved interview question."""

    id: uuid.UUID
    question: str
    focus_area: str
    difficulty: str
    guideline: str
    is_follow_up: bool = False


class QuestionSetRead(BaseModel):
    """A candidate's saved interview question set."""

    candidate_id: uuid.UUID
    interview_id: uuid.UUID | None = None
    questions: list[StoredQuestionRead] = Field(default_factory=list)


class QuestionUpdate(BaseModel):
    """Request body for `PUT /interview/questions/{question_id}`."""

    question: str | None = Field(default=None, min_length=1)
    focus_area: str | None = Field(default=None, min_length=1)
    difficulty: str | None = None
    guideline: str | None = Field(default=None, min_length=1)
