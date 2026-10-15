"""Candidate listing, assessment, and pipeline endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.core.constants import INTERVIEW_ROLES
from app.core.dependencies import (
    get_candidate_service,
    get_interview_service,
    get_resume_service,
    require_candidate,
    require_hr,
    require_roles,
)
from app.exceptions.errors import ValidationAppError
from app.models.user import User
from app.schemas.candidate import (
    AssessmentRead,
    CandidateApplicationRead,
    CandidateNoteCreate,
    CandidateNoteRead,
    CandidateProfileUpdate,
    CandidateRead,
    CandidateStatusEventRead,
    CandidateStatusUpdate,
    ScoreOverrideRequest,
)
from app.schemas.interview import QuestionSetRead
from app.schemas.resume import ResumeUploadResponse
from app.services.candidate_service import CandidateService
from app.services.interview_service import InterviewService
from app.services.resume_service import ResumeService

_MAX_RESUME_BYTES = 10 * 1024 * 1024

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post(
    "/apply",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to an open job",
    description="Uploads a PDF resume, parses it, and creates an application owned by the "
    "authenticated candidate. Duplicate applications to the same job are rejected.",
    responses={
        404: {"description": "Job not found or not open."},
        409: {"description": "The candidate has already applied to this job."},
        422: {"description": "File is not a valid PDF."},
    },
)
async def apply_to_job(
    job_id: uuid.UUID = Form(..., description="The open job to apply to."),
    file: UploadFile = File(..., description="The candidate's resume, as a PDF file."),
    current_user: User = Depends(require_candidate()),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeUploadResponse:
    """Apply to an open job with a PDF resume.

    Args:
        job_id: The job to apply to.
        file: The uploaded PDF resume.
        current_user: The authenticated candidate.
        resume_service: Injected `ResumeService`.

    Returns:
        The parsed profile and application ids.

    Raises:
        ValidationAppError: If the uploaded file is not a PDF, or is too large.
    """

    if file.content_type != "application/pdf":
        raise ValidationAppError("Only PDF resumes are accepted.")

    contents = await file.read()
    if len(contents) > _MAX_RESUME_BYTES:
        raise ValidationAppError("Resume file must be 10MB or smaller.")

    resume, candidate, parsed_candidate = await resume_service.apply_as_candidate(
        user=current_user,
        job_id=job_id,
        original_filename=file.filename or "resume.pdf",
        file_bytes=contents,
    )
    return ResumeUploadResponse(
        resume_id=resume.id,
        candidate_id=candidate.id,
        parsed_profile=parsed_candidate.model_dump(),
    )


@router.get(
    "/me",
    response_model=list[CandidateApplicationRead],
    summary="List my applications",
    description="Returns the authenticated candidate's applications and statuses. Recruiter "
    "notes, scores, and other applicants are never included.",
)
async def list_my_applications(
    current_user: User = Depends(require_candidate()),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> list[CandidateApplicationRead]:
    """List the current candidate's applications.

    Args:
        current_user: The authenticated candidate.
        candidate_service: Injected `CandidateService`.

    Returns:
        The user's applications, newest first.
    """

    return await candidate_service.list_mine(current_user.id)


@router.get(
    "/me/{candidate_id}",
    response_model=CandidateApplicationRead,
    summary="Get one of my applications",
    responses={404: {"description": "Application not found."}},
)
async def get_my_application(
    candidate_id: uuid.UUID,
    current_user: User = Depends(require_candidate()),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateApplicationRead:
    """Fetch one application owned by the current candidate.

    Args:
        candidate_id: The application id.
        current_user: The authenticated candidate.
        candidate_service: Injected `CandidateService`.

    Returns:
        Status and parsed resume only.
    """

    return await candidate_service.get_own_application(candidate_id, current_user.id)


@router.patch(
    "/me/{candidate_id}/profile",
    response_model=CandidateApplicationRead,
    summary="Correct my parsed resume",
    responses={404: {"description": "Application not found."}, 422: {"description": "Resume has not been parsed."}},
)
async def update_my_profile(
    candidate_id: uuid.UUID,
    payload: CandidateProfileUpdate,
    current_user: User = Depends(require_candidate()),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateApplicationRead:
    """Correct parsed fields on an application the candidate owns.

    Args:
        candidate_id: The application id.
        payload: Fields to replace.
        current_user: The authenticated candidate.
        candidate_service: Injected `CandidateService`.

    Returns:
        The updated application.
    """

    candidate = await candidate_service.update_own_profile(candidate_id, current_user.id, payload)
    return await candidate_service.to_application_read(candidate)


@router.get(
    "/{candidate_id}",
    response_model=CandidateRead,
    summary="Get a candidate",
    description="Fetches a single candidate's record, including parsed profile and pipeline status.",
    dependencies=[Depends(require_hr())],
    responses={404: {"description": "Candidate not found."}},
)
async def get_candidate(
    candidate_id: uuid.UUID, candidate_service: CandidateService = Depends(get_candidate_service)
) -> CandidateRead:
    """Fetch a single candidate by id.

    Args:
        candidate_id: The candidate's id.
        candidate_service: Injected `CandidateService`.

    Returns:
        The matching candidate record.
    """

    candidate = await candidate_service.get_candidate(candidate_id)
    return CandidateRead.model_validate(candidate)


@router.get(
    "",
    response_model=list[CandidateRead],
    summary="List candidates for a job",
    description="Lists all candidates evaluated against a given job, with pagination.",
    dependencies=[Depends(require_hr())],
)
async def list_candidates_for_job(
    job_id: uuid.UUID = Query(..., description="Job id to list candidates for."),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> list[CandidateRead]:
    """List candidates evaluated against a specific job.

    Args:
        job_id: The job to filter candidates by.
        offset: Number of rows to skip.
        limit: Maximum number of rows to return.
        candidate_service: Injected `CandidateService`.

    Returns:
        A list of matching candidate records.
    """

    candidates = await candidate_service.list_for_job(job_id=job_id, offset=offset, limit=limit)
    return [CandidateRead.model_validate(candidate) for candidate in candidates]


@router.get(
    "/{candidate_id}/assessment",
    response_model=AssessmentRead,
    summary="Get a stored assessment",
    description="Returns the latest score and matcher explanation. Does not re-run the AI workflow.",
    dependencies=[Depends(require_hr())],
    responses={404: {"description": "Candidate not found, or no score has been stored yet."}},
)
async def get_assessment(
    candidate_id: uuid.UUID, candidate_service: CandidateService = Depends(get_candidate_service)
) -> AssessmentRead:
    """Read the stored assessment for a candidate.

    Args:
        candidate_id: The candidate's id.
        candidate_service: Injected `CandidateService`.

    Returns:
        Score breakdown, skill gaps, and the matcher explanation.
    """

    return await candidate_service.get_assessment(candidate_id)


@router.patch(
    "/{candidate_id}/status",
    response_model=CandidateRead,
    summary="Change pipeline status",
    description="Shortlist, reject, or advance a candidate. Illegal jumps are rejected.",
    responses={404: {"description": "Candidate not found."}, 422: {"description": "Illegal status transition."}},
)
async def change_status(
    candidate_id: uuid.UUID,
    payload: CandidateStatusUpdate,
    current_user: User = Depends(require_hr()),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateRead:
    """Move a candidate to a new pipeline status.

    Args:
        candidate_id: The candidate's id.
        payload: The requested status.
        current_user: The staff user making the change.
        candidate_service: Injected `CandidateService`.

    Returns:
        The updated candidate. Private notes are not included.
    """

    candidate = await candidate_service.change_status(candidate_id, payload.status, current_user.id)
    return CandidateRead.model_validate(candidate)


@router.post(
    "/{candidate_id}/notes",
    response_model=CandidateNoteRead,
    status_code=201,
    summary="Add a private note",
    description="Stores a recruiter note. Notes are not returned on the candidate record.",
    responses={404: {"description": "Candidate not found."}},
)
async def add_note(
    candidate_id: uuid.UUID,
    payload: CandidateNoteCreate,
    current_user: User = Depends(require_hr()),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateNoteRead:
    """Add a private note to a candidate.

    Args:
        candidate_id: The candidate's id.
        payload: The note text.
        current_user: The staff user writing the note.
        candidate_service: Injected `CandidateService`.

    Returns:
        The saved note.
    """

    note = await candidate_service.add_note(candidate_id, current_user.id, payload.body)
    return CandidateNoteRead.model_validate(note)


@router.get(
    "/{candidate_id}/notes",
    response_model=list[CandidateNoteRead],
    summary="List private notes",
    dependencies=[Depends(require_hr())],
    responses={404: {"description": "Candidate not found."}},
)
async def list_notes(
    candidate_id: uuid.UUID, candidate_service: CandidateService = Depends(get_candidate_service)
) -> list[CandidateNoteRead]:
    """List private notes for a candidate, newest first.

    Args:
        candidate_id: The candidate's id.
        candidate_service: Injected `CandidateService`.

    Returns:
        The candidate's notes.
    """

    return await candidate_service.list_notes(candidate_id)


@router.get(
    "/{candidate_id}/events",
    response_model=list[CandidateStatusEventRead],
    summary="List status history",
    dependencies=[Depends(require_hr())],
    responses={404: {"description": "Candidate not found."}},
)
async def list_events(
    candidate_id: uuid.UUID, candidate_service: CandidateService = Depends(get_candidate_service)
) -> list[CandidateStatusEventRead]:
    """List pipeline status changes, oldest first.

    Args:
        candidate_id: The candidate's id.
        candidate_service: Injected `CandidateService`.

    Returns:
        The audit trail.
    """

    return await candidate_service.list_events(candidate_id)


@router.patch(
    "/{candidate_id}/profile",
    response_model=CandidateRead,
    summary="Correct a parsed profile",
    description="Replaces selected parsed fields and clears the stored match explanation.",
    dependencies=[Depends(require_hr())],
    responses={404: {"description": "Candidate not found."}, 422: {"description": "Resume has not been parsed."}},
)
async def update_profile(
    candidate_id: uuid.UUID,
    payload: CandidateProfileUpdate,
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateRead:
    """Correct extracted resume fields.

    Args:
        candidate_id: The candidate's id.
        payload: Fields to replace.
        candidate_service: Injected `CandidateService`.

    Returns:
        The updated candidate. Run the hiring workflow again to refresh the score.
    """

    candidate = await candidate_service.update_profile(candidate_id, payload)
    return CandidateRead.model_validate(candidate)


@router.patch(
    "/{candidate_id}/score",
    response_model=CandidateRead,
    summary="Override the total score",
    description="Sets the latest total score without calling the model, and stores the reason as a note.",
    responses={404: {"description": "Candidate or score not found."}},
)
async def override_score(
    candidate_id: uuid.UUID,
    payload: ScoreOverrideRequest,
    current_user: User = Depends(require_hr()),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateRead:
    """Replace the latest total score with a recruiter's value.

    Args:
        candidate_id: The candidate's id.
        payload: The new total and the reason.
        current_user: The staff user making the override.
        candidate_service: Injected `CandidateService`.

    Returns:
        The updated candidate.
    """

    candidate = await candidate_service.override_score(
        candidate_id, payload.total_score, payload.reason, current_user.id
    )
    return CandidateRead.model_validate(candidate)


@router.post(
    "/{candidate_id}/questions/generate",
    response_model=QuestionSetRead,
    summary="Generate a question set",
    description="Creates a beginner, intermediate, advanced, and project question and saves them.",
    dependencies=[Depends(require_roles(*INTERVIEW_ROLES))],
    responses={404: {"description": "Candidate not found or not yet parsed."}},
)
async def generate_questions(
    candidate_id: uuid.UUID, interview_service: InterviewService = Depends(get_interview_service)
) -> QuestionSetRead:
    """Generate and save an interview question set.

    Args:
        candidate_id: The candidate's id.
        interview_service: Injected `InterviewService`.

    Returns:
        The saved question set.
    """

    return await interview_service.generate_question_set(candidate_id)


@router.post(
    "/{candidate_id}/questions/regenerate",
    response_model=QuestionSetRead,
    summary="Regenerate a question set",
    description="Replaces the saved question set with a newly generated one.",
    dependencies=[Depends(require_roles(*INTERVIEW_ROLES))],
    responses={404: {"description": "Candidate not found or not yet parsed."}},
)
async def regenerate_questions(
    candidate_id: uuid.UUID, interview_service: InterviewService = Depends(get_interview_service)
) -> QuestionSetRead:
    """Replace the saved question set.

    Args:
        candidate_id: The candidate's id.
        interview_service: Injected `InterviewService`.

    Returns:
        The new question set.
    """

    return await interview_service.generate_question_set(candidate_id)


@router.get(
    "/{candidate_id}/questions",
    response_model=QuestionSetRead,
    summary="List saved questions",
    dependencies=[Depends(require_roles(*INTERVIEW_ROLES))],
    responses={404: {"description": "Candidate not found."}},
)
async def list_questions(
    candidate_id: uuid.UUID, interview_service: InterviewService = Depends(get_interview_service)
) -> QuestionSetRead:
    """Return the saved question set.

    Args:
        candidate_id: The candidate's id.
        interview_service: Injected `InterviewService`.

    Returns:
        The saved set, or an empty list if none has been generated.
    """

    return await interview_service.list_questions(candidate_id)
