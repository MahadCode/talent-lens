"""Business logic for job posting management."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from app.core.constants import HR_ROLES, JobStatus
from app.exceptions.errors import NotFoundError
from app.models.job import Job
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobCreate, JobUpdate
from app.services.requirement_extractor import extract_requirements


class JobService:
    """Coordinates creating, reading, updating, and deleting `Job` postings."""

    def __init__(
        self,
        job_repo: JobRepository,
        extractor: Callable[[str, str], dict] | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            job_repo: Repository for `Job` persistence.
            extractor: Optional replacement for the LLM requirement extractor,
                used by tests.
        """

        self._job_repo = job_repo
        self._extractor = extractor or extract_requirements

    async def create_job(self, created_by_id: uuid.UUID, data: JobCreate) -> Job:
        """Create a new job posting.

        Args:
            created_by_id: Id of the HR user creating the posting.
            data: The validated job creation payload.

        Returns:
            The created `Job`.
        """

        job = Job(
            title=data.title,
            description=data.description,
            requirements=data.requirements,
            status=data.status,
            created_by_id=created_by_id,
        )
        return await self._job_repo.add(job)

    async def get_job(self, job_id: uuid.UUID) -> Job:
        """Fetch a job by id.

        Args:
            job_id: The job's id.

        Returns:
            The matching `Job`.

        Raises:
            NotFoundError: If no job with this id exists.
        """

        job = await self._job_repo.get_by_id(job_id)
        if job is None:
            raise NotFoundError("Job not found.")
        return job

    async def list_jobs(
        self, status_filter: JobStatus | None = None, offset: int = 0, limit: int = 20
    ) -> list[Job]:
        """List job postings, optionally filtered by status.

        Args:
            status_filter: If provided, only jobs with this status are returned.
            offset: Number of rows to skip.
            limit: Maximum number of rows to return.

        Returns:
            A list of `Job` instances.
        """

        return await self._job_repo.list_by_status(status=status_filter, offset=offset, limit=limit)

    async def list_open_jobs(self, offset: int = 0, limit: int = 20) -> list[Job]:
        """List jobs that candidates may apply to.

        Args:
            offset: Number of rows to skip.
            limit: Maximum number of rows to return.

        Returns:
            Open job postings only.
        """

        return await self._job_repo.list_by_status(status=JobStatus.OPEN, offset=offset, limit=limit)

    async def get_job_for_viewer(self, job_id: uuid.UUID, viewer: User) -> Job:
        """Fetch a job, hiding non-open postings from non-HR viewers.

        Args:
            job_id: The job's id.
            viewer: The authenticated user requesting the job.

        Returns:
            The matching `Job`.

        Raises:
            NotFoundError: If the job does not exist, or a candidate asked
                for a job that is not open.
        """

        job = await self.get_job(job_id)
        if viewer.role in HR_ROLES:
            return job
        if job.status != JobStatus.OPEN:
            raise NotFoundError("Job not found.")
        return job

    async def update_job(self, job_id: uuid.UUID, data: JobUpdate) -> Job:
        """Update fields on an existing job posting.

        Args:
            job_id: The id of the job to update.
            data: Fields to change; unset fields are left untouched.

        Returns:
            The updated `Job`.

        Raises:
            NotFoundError: If no job with this id exists.
        """

        job = await self.get_job(job_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(job, field, value)
        return job

    async def delete_job(self, job_id: uuid.UUID) -> None:
        """Delete a job posting.

        Args:
            job_id: The id of the job to delete.

        Raises:
            NotFoundError: If no job with this id exists.
        """

        job = await self.get_job(job_id)
        await self._job_repo.delete(job)

    async def extract_requirements(self, job_id: uuid.UUID, apply: bool) -> tuple[dict, bool]:
        """Extract structured requirements from the job's free text.

        Args:
            job_id: The job to read.
            apply: When true, persist the extraction on the job.

        Returns:
            The extracted payload and whether it was saved.

        Raises:
            NotFoundError: If no job with this id exists.
        """

        job = await self.get_job(job_id)
        extracted = self._extractor(job.description, job.requirements)
        if apply:
            job.extracted_requirements = extracted
        return extracted, apply
