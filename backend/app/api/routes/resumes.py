"""Resume upload endpoint: extraction + parsing via the Resume Parser Agent."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.core.dependencies import get_resume_service, require_candidate, require_hr
from app.exceptions.errors import ValidationAppError
from app.models.user import User
from app.schemas.resume import ResumeSelfRead, ResumeUploadResponse
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resumes", tags=["Resumes"])

_MAX_RESUME_BYTES = 10 * 1024 * 1024


@router.get(
    "/me",
    response_model=ResumeSelfRead,
    summary="Get my parsed resume",
    description="Returns the authenticated candidate's parsed resume. Pass candidate_id to "
    "pick a specific application; otherwise the latest application is used.",
    responses={404: {"description": "No resume found for this account."}},
)
async def get_my_resume(
    candidate_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(require_candidate()),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeSelfRead:
    """Return a parsed resume owned by the current candidate.

    Args:
        candidate_id: Optional application id.
        current_user: The authenticated candidate.
        resume_service: Injected `ResumeService`.

    Returns:
        The parsed resume without recruiter scores or notes.
    """

    resume, candidate = await resume_service.get_resume_for_owner(current_user.id, candidate_id)
    return ResumeSelfRead(
        resume_id=resume.id,
        candidate_id=candidate.id,
        job_id=candidate.job_id,
        original_filename=resume.original_filename,
        parsed_profile=candidate.parsed_profile,
    )


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a resume",
    description="Accepts a job id and a PDF resume, extracts its text, invokes the Resume "
    "Parser Agent, and returns the structured parsed profile. HR roles only.",
    dependencies=[Depends(require_hr())],
    responses={422: {"description": "File is not a valid PDF, or no extractable text was found."}},
)
async def upload_resume(
    job_id: uuid.UUID = Form(..., description="The job this resume is being submitted for."),
    candidate_id: uuid.UUID | None = Form(
        default=None, description="Existing candidate id to attach this resume to, if any."
    ),
    file: UploadFile = File(..., description="The candidate's resume, as a PDF file."),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeUploadResponse:
    """Upload a resume PDF and parse it into a structured candidate profile.

    Args:
        job_id: The job this resume is being submitted for.
        candidate_id: An existing candidate id to attach this resume to,
            or None to create a new candidate.
        file: The uploaded PDF file.
        resume_service: Injected `ResumeService`.

    Returns:
        The parsed candidate profile and identifying ids.

    Raises:
        ValidationAppError: If the uploaded file is not a PDF.
    """

    if file.content_type != "application/pdf":
        raise ValidationAppError("Only PDF resumes are accepted.")

    contents = await file.read()
    if len(contents) > _MAX_RESUME_BYTES:
        raise ValidationAppError("Resume file must be 10MB or smaller.")

    resume, candidate, parsed_candidate = await resume_service.upload_and_parse(
        job_id=job_id,
        candidate_id=candidate_id,
        original_filename=file.filename or "resume.pdf",
        file_bytes=contents,
    )

    return ResumeUploadResponse(
        resume_id=resume.id,
        candidate_id=candidate.id,
        parsed_profile=parsed_candidate.model_dump(),
    )
