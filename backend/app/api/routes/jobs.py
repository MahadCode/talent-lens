"""Job posting endpoints. Create/update/delete are restricted to HR roles."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.constants import JobStatus
from app.core.dependencies import get_current_user, get_job_service, require_hr
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.job import ExtractRequirementsRequest, ExtractRequirementsResponse, JobCreate, JobRead, JobUpdate
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job posting",
    description="Creates a new job posting. Only authenticated HR staff (ADMIN, HR_MANAGER, "
    "or RECRUITER) may create jobs.",
    dependencies=[Depends(require_hr())],
)
async def create_job(
    payload: JobCreate,
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:
    """Create a new job posting.

    Args:
        payload: The job creation payload.
        current_user: The authenticated HR user creating the job.
        job_service: Injected `JobService`.

    Returns:
        The created job posting.
    """

    job = await job_service.create_job(created_by_id=current_user.id, data=payload)
    return JobRead.model_validate(job)


@router.get(
    "",
    response_model=list[JobRead],
    summary="List job postings",
    description="Lists job postings, optionally filtered by status. HR roles only.",
    dependencies=[Depends(require_hr())],
)
async def list_jobs(
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    job_service: JobService = Depends(get_job_service),
) -> list[JobRead]:
    """List job postings with optional status filtering and pagination.

    Args:
        status_filter: Optional job status to filter by.
        offset: Number of rows to skip.
        limit: Maximum number of rows to return.
        job_service: Injected `JobService`.

    Returns:
        A list of job postings.
    """

    jobs = await job_service.list_jobs(status_filter=status_filter, offset=offset, limit=limit)
    return [JobRead.model_validate(job) for job in jobs]


@router.get(
    "/open",
    response_model=list[JobRead],
    summary="List open vacancies",
    description="Lists jobs that candidates may apply to. Draft and closed jobs are omitted.",
)
async def list_open_jobs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
) -> list[JobRead]:
    """List open job postings for authenticated users.

    Args:
        offset: Number of rows to skip.
        limit: Maximum number of rows to return.
        current_user: The authenticated viewer.
        job_service: Injected `JobService`.

    Returns:
        Open job postings.
    """

    del current_user
    jobs = await job_service.list_open_jobs(offset=offset, limit=limit)
    return [JobRead.model_validate(job) for job in jobs]


@router.get(
    "/{job_id}",
    response_model=JobRead,
    summary="Get a job posting",
    description="HR staff may fetch any job. Candidates only see open vacancies.",
    responses={404: {"description": "Job not found."}},
)
async def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
) -> JobRead:
    """Fetch a single job posting by id.

    Args:
        job_id: The job's id.
        current_user: The authenticated viewer.
        job_service: Injected `JobService`.

    Returns:
        The matching job posting.
    """

    job = await job_service.get_job_for_viewer(job_id, current_user)
    return JobRead.model_validate(job)


@router.put(
    "/{job_id}",
    response_model=JobRead,
    summary="Update a job posting",
    description="Updates fields on an existing job posting. HR roles only.",
    dependencies=[Depends(require_hr())],
    responses={404: {"description": "Job not found."}},
)
async def update_job(
    job_id: uuid.UUID, payload: JobUpdate, job_service: JobService = Depends(get_job_service)
) -> JobRead:
    """Update a job posting.

    Args:
        job_id: The id of the job to update.
        payload: Fields to update.
        job_service: Injected `JobService`.

    Returns:
        The updated job posting.
    """

    job = await job_service.update_job(job_id, payload)
    return JobRead.model_validate(job)


@router.delete(
    "/{job_id}",
    response_model=MessageResponse,
    summary="Delete a job posting",
    description="Permanently deletes a job posting and its associated candidates. HR roles only.",
    dependencies=[Depends(require_hr())],
    responses={404: {"description": "Job not found."}},
)
async def delete_job(
    job_id: uuid.UUID, job_service: JobService = Depends(get_job_service)
) -> MessageResponse:
    """Delete a job posting.

    Args:
        job_id: The id of the job to delete.
        job_service: Injected `JobService`.

    Returns:
        A confirmation message.
    """

    await job_service.delete_job(job_id)
    return MessageResponse(message="Job deleted successfully.")


@router.post(
    "/{job_id}/extract-requirements",
    response_model=ExtractRequirementsResponse,
    summary="Extract structured requirements",
    description="Reads the job text with the LLM. Pass apply=true to save the result on the job.",
    dependencies=[Depends(require_hr())],
    responses={404: {"description": "Job not found."}},
)
async def extract_job_requirements(
    job_id: uuid.UUID,
    payload: ExtractRequirementsRequest,
    job_service: JobService = Depends(get_job_service),
) -> ExtractRequirementsResponse:
    """Extract required skills, experience, and qualifications from the job text.

    Args:
        job_id: The job to read.
        payload: Whether to persist the extraction.
        job_service: Injected `JobService`.

    Returns:
        The structured requirements.
    """

    extracted, applied = await job_service.extract_requirements(job_id, payload.apply)
    return ExtractRequirementsResponse(**extracted, applied=applied)
