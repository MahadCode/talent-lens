"""Business logic for resume upload and parsing.

This service is the only place, outside of `WorkflowService`, that calls
into the AI agent layer directly — specifically the `ResumeParserAgent` —
since parsing a freshly uploaded resume is a standalone operation that
does not require running the full hiring workflow.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from ai_agents.agents.parser_agent import ResumeParserAgent
from ai_agents.utils.schemas import ParsedCandidate
from app.core.config import get_settings
from app.core.constants import CandidateStatus, JobStatus
from app.exceptions.errors import ConflictError, NotFoundError
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.models.user import User
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.utils.pdf_extract import extract_text_from_pdf


class ResumeService:
    """Coordinates resume storage, text extraction, and AI parsing."""

    def __init__(
        self,
        resume_repo: ResumeRepository,
        candidate_repo: CandidateRepository,
        job_repo: JobRepository | None = None,
        parser_agent: ResumeParserAgent | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            resume_repo: Repository for `Resume` persistence.
            candidate_repo: Repository for `Candidate` persistence.
            job_repo: Repository for `Job` persistence. Required for candidate apply.
            parser_agent: Optional agent override, primarily for testing.
                Defaults to a new `ResumeParserAgent` instance.
        """

        self._resume_repo = resume_repo
        self._candidate_repo = candidate_repo
        self._job_repo = job_repo
        self._parser_agent = parser_agent or ResumeParserAgent()

    async def upload_and_parse(
        self,
        job_id: uuid.UUID,
        candidate_id: uuid.UUID | None,
        original_filename: str,
        file_bytes: bytes,
    ) -> tuple[Resume, Candidate, ParsedCandidate]:
        """Store an uploaded PDF resume, extract its text, and parse it.

        Args:
            job_id: The job this resume is being submitted for.
            candidate_id: An existing candidate id to attach this resume
                to, or None to create a new candidate.
            original_filename: The filename as uploaded by the client.
            file_bytes: The raw PDF file bytes.

        Returns:
            A tuple of the persisted `Resume`, the associated `Candidate`
            (created if `candidate_id` was None), and the structured
            `ParsedCandidate` produced by the Resume Parser Agent.

        Raises:
            NotFoundError: If `candidate_id` was provided but does not exist.
        """

        if candidate_id is not None:
            candidate = await self._candidate_repo.get_by_id(candidate_id)
            if candidate is None:
                raise NotFoundError("Candidate not found.")
        else:
            candidate = await self._candidate_repo.add(
                Candidate(job_id=job_id, status=CandidateStatus.NEW, score_overridden=False)
            )

        file_path = self._persist_file(candidate.id, original_filename, file_bytes)
        extracted_text = extract_text_from_pdf(file_bytes)

        resume = Resume(
            candidate_id=candidate.id,
            file_path=file_path,
            original_filename=original_filename,
            extracted_text=extracted_text,
        )
        resume = await self._resume_repo.add(resume)

        parsed_candidate = self._parser_agent.run(resume_text=extracted_text)

        candidate.full_name = parsed_candidate.name
        candidate.email = parsed_candidate.email
        candidate.github_url = parsed_candidate.github
        candidate.parsed_profile = parsed_candidate.model_dump()
        candidate.status = CandidateStatus.PARSED

        return resume, candidate, parsed_candidate

    async def apply_as_candidate(
        self,
        user: User,
        job_id: uuid.UUID,
        original_filename: str,
        file_bytes: bytes,
    ) -> tuple[Resume, Candidate, ParsedCandidate]:
        """Create an application owned by a candidate account and parse the resume.

        Args:
            user: The authenticated candidate.
            job_id: The open job they are applying to.
            original_filename: The filename as uploaded by the client.
            file_bytes: The raw PDF file bytes.

        Returns:
            The persisted resume, candidate application, and parsed profile.

        Raises:
            NotFoundError: If the job does not exist or is not open.
            ConflictError: If this user has already applied to the job.
        """

        if self._job_repo is None:
            raise NotFoundError("Job not found.")
        job = await self._job_repo.get_by_id(job_id)
        if job is None or job.status != JobStatus.OPEN:
            raise NotFoundError("Job not found.")

        existing = await self._candidate_repo.get_by_user_and_job(user.id, job_id)
        if existing is not None:
            raise ConflictError("You have already applied to this job.")

        candidate = await self._candidate_repo.add(
            Candidate(
                job_id=job_id,
                user_id=user.id,
                status=CandidateStatus.NEW,
                score_overridden=False,
                full_name=user.full_name,
                email=user.email,
            )
        )
        return await self.upload_and_parse(
            job_id=job_id,
            candidate_id=candidate.id,
            original_filename=original_filename,
            file_bytes=file_bytes,
        )

    async def get_resume_for_owner(
        self, user_id: uuid.UUID, candidate_id: uuid.UUID | None = None
    ) -> tuple[Resume, Candidate]:
        """Return a parsed resume the candidate account owns.

        Args:
            user_id: The candidate account.
            candidate_id: A specific application, or None for the latest one.

        Returns:
            The resume and its candidate row.

        Raises:
            NotFoundError: If the user has no matching application or resume.
        """

        if candidate_id is not None:
            candidate = await self._candidate_repo.get_by_id(candidate_id)
            if candidate is None or candidate.user_id != user_id:
                raise NotFoundError("Resume not found.")
        else:
            owned = await self._candidate_repo.list_by_user(user_id)
            if not owned:
                raise NotFoundError("Resume not found.")
            candidate = owned[0]

        resume = await self._resume_repo.get_latest_for_candidate(candidate.id)
        if resume is None:
            raise NotFoundError("Resume not found.")
        return resume, candidate

    def _persist_file(self, candidate_id: uuid.UUID, original_filename: str, file_bytes: bytes) -> str:
        """Write the uploaded file to the configured upload directory.

        Args:
            candidate_id: The candidate this file belongs to, used to
                namespace stored files.
            original_filename: The filename as uploaded by the client.
            file_bytes: The raw file bytes to write.

        Returns:
            The filesystem path the file was written to.
        """

        settings = get_settings()
        candidate_dir = Path(settings.upload_dir) / str(candidate_id)
        candidate_dir.mkdir(parents=True, exist_ok=True)

        safe_name = Path(original_filename).name  # strip any path components
        destination = candidate_dir / f"{uuid.uuid4()}_{safe_name}"
        destination.write_bytes(file_bytes)
        return str(destination)
