"""Interview endpoints: adaptive question generation and transcript evaluation."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_interview_service, require_roles
from app.core.constants import INTERVIEW_ROLES
from app.schemas.interview import (
    InterviewEvaluateRequest,
    InterviewEvaluateResponse,
    InterviewQuestionRequest,
    InterviewQuestionResponse,
    QuestionSetRead,
    QuestionUpdate,
    StoredQuestionRead,
)
from app.services.interview_service import InterviewService

router = APIRouter(
    prefix="/interview", tags=["Interviews"], dependencies=[Depends(require_roles(*INTERVIEW_ROLES))]
)


@router.post(
    "/questions",
    response_model=InterviewQuestionResponse,
    summary="Generate the next adaptive interview question",
    description="Generates a single adaptive interview question, optionally a follow-up, based "
    "on the job description, candidate skills, and prior conversation history. Reuses the "
    "existing Interview Agent.",
    responses={404: {"description": "Candidate not found or not yet parsed."}},
)
async def get_next_question(
    payload: InterviewQuestionRequest,
    interview_service: InterviewService = Depends(get_interview_service),
) -> InterviewQuestionResponse:
    """Generate the next interview question for a candidate.

    Args:
        payload: The candidate/job context and prior conversation history.
        interview_service: Injected `InterviewService`.

    Returns:
        The next question to ask.
    """

    return await interview_service.next_question(
        candidate_id=payload.candidate_id,
        job_description=payload.job_description,
        conversation_history=payload.conversation_history,
    )


@router.post(
    "/evaluate",
    response_model=InterviewEvaluateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Evaluate a completed interview transcript",
    description="Evaluates a full interview transcript and persists the result, including a "
    "pass/fail determination.",
    responses={404: {"description": "Candidate not found."}},
)
async def evaluate_interview(
    payload: InterviewEvaluateRequest,
    interview_service: InterviewService = Depends(get_interview_service),
) -> InterviewEvaluateResponse:
    """Evaluate a completed interview transcript.

    Args:
        payload: The candidate id and full Q&A transcript.
        interview_service: Injected `InterviewService`.

    Returns:
        The persisted evaluation result.
    """

    interview = await interview_service.evaluate_transcript(
        candidate_id=payload.candidate_id, questions_and_answers=payload.questions_and_answers
    )
    return InterviewEvaluateResponse(
        interview_id=interview.id,
        overall_assessment=interview.overall_assessment or "",
        passed=bool(interview.passed),
    )


@router.put(
    "/questions/{question_id}",
    response_model=StoredQuestionRead,
    summary="Edit a saved interview question",
    responses={404: {"description": "Question not found."}, 422: {"description": "No fields to update."}},
)
async def update_question(
    question_id: uuid.UUID,
    payload: QuestionUpdate,
    interview_service: InterviewService = Depends(get_interview_service),
) -> StoredQuestionRead:
    """Edit one question in the saved set.

    Args:
        question_id: The question id.
        payload: Fields to change.
        interview_service: Injected `InterviewService`.

    Returns:
        The edited question.
    """

    return await interview_service.update_question(question_id, payload)


@router.delete(
    "/questions/{question_id}",
    response_model=QuestionSetRead,
    summary="Remove a saved interview question",
    responses={404: {"description": "Question not found."}},
)
async def delete_question(
    question_id: uuid.UUID,
    interview_service: InterviewService = Depends(get_interview_service),
) -> QuestionSetRead:
    """Remove one question from the saved set.

    Args:
        question_id: The question id.
        interview_service: Injected `InterviewService`.

    Returns:
        The question set that remains.
    """

    return await interview_service.delete_question(question_id)
