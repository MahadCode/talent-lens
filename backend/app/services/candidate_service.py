"""Business logic for candidate records, assessments, and pipeline actions."""

from __future__ import annotations

import uuid

from app.core.constants import CandidateStatus
from app.exceptions.errors import NotFoundError, ValidationAppError
from app.models.candidate import Candidate
from app.models.candidate_note import CandidateNote
from app.models.candidate_status_event import CandidateStatusEvent
from app.repositories.candidate_note_repository import CandidateNoteRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_status_event_repository import CandidateStatusEventRepository
from app.repositories.job_repository import JobRepository
from app.repositories.score_repository import ScoreRepository
from app.schemas.candidate import (
    AssessmentRead,
    CandidateApplicationRead,
    CandidateNoteRead,
    CandidateProfileUpdate,
    CandidateStatusEventRead,
)
from app.services.pipeline_rules import assert_transition


class CandidateService:
    """Coordinates reading and updating `Candidate` records."""

    def __init__(
        self,
        candidate_repo: CandidateRepository,
        score_repo: ScoreRepository | None = None,
        note_repo: CandidateNoteRepository | None = None,
        event_repo: CandidateStatusEventRepository | None = None,
        job_repo: JobRepository | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            candidate_repo: Repository for `Candidate` persistence.
            score_repo: Repository for `Score` persistence.
            note_repo: Repository for private notes.
            event_repo: Repository for status audit events.
            job_repo: Repository for `Job` persistence. Used to attach job titles
                to a candidate's own applications.
        """

        self._candidate_repo = candidate_repo
        self._score_repo = score_repo
        self._note_repo = note_repo
        self._event_repo = event_repo
        self._job_repo = job_repo

    async def get_candidate(self, candidate_id: uuid.UUID) -> Candidate:
        """Fetch a candidate by id.

        Args:
            candidate_id: The candidate's id.

        Returns:
            The matching `Candidate`.

        Raises:
            NotFoundError: If no candidate with this id exists.
        """

        candidate = await self._candidate_repo.get_by_id(candidate_id)
        if candidate is None:
            raise NotFoundError("Candidate not found.")
        return candidate

    async def list_for_job(self, job_id: uuid.UUID, offset: int = 0, limit: int = 20) -> list[Candidate]:
        """List candidates evaluated against a specific job.

        Args:
            job_id: The job to filter candidates by.
            offset: Number of rows to skip.
            limit: Maximum number of rows to return.

        Returns:
            A list of `Candidate` instances.
        """

        return await self._candidate_repo.list_by_job(job_id=job_id, offset=offset, limit=limit)

    async def get_or_create_for_job(self, job_id: uuid.UUID, candidate_id: uuid.UUID | None) -> Candidate:
        """Fetch an existing candidate or create a new one for a job.

        Args:
            job_id: The job the candidate is being evaluated for.
            candidate_id: An existing candidate id to reuse (e.g. when
                uploading a second resume for the same person), or None to
                create a brand-new candidate record.

        Returns:
            The existing or newly created `Candidate`.

        Raises:
            NotFoundError: If `candidate_id` was provided but does not exist.
        """

        if candidate_id is not None:
            return await self.get_candidate(candidate_id)

        candidate = Candidate(job_id=job_id, status=CandidateStatus.NEW, score_overridden=False)
        return await self._candidate_repo.add(candidate)

    async def get_owned(self, candidate_id: uuid.UUID, user_id: uuid.UUID) -> Candidate:
        """Fetch an application only if the candidate account owns it.

        Args:
            candidate_id: The application id.
            user_id: The candidate account.

        Returns:
            The matching `Candidate`.

        Raises:
            NotFoundError: If the application is missing or belongs to someone else.
        """

        candidate = await self.get_candidate(candidate_id)
        if candidate.user_id != user_id:
            raise NotFoundError("Candidate not found.")
        return candidate

    async def list_mine(self, user_id: uuid.UUID) -> list[CandidateApplicationRead]:
        """List the authenticated candidate's applications.

        The payload is status and parsed resume only. Recruiter notes, scores,
        and matcher explanations are omitted.

        Args:
            user_id: The candidate account.

        Returns:
            The user's applications, newest first.
        """

        candidates = await self._candidate_repo.list_by_user(user_id)
        return [await self.to_application_read(candidate) for candidate in candidates]

    async def get_own_application(
        self, candidate_id: uuid.UUID, user_id: uuid.UUID
    ) -> CandidateApplicationRead:
        """Return one owned application without recruiter-only fields.

        Args:
            candidate_id: The application id.
            user_id: The candidate account.

        Returns:
            Status, job title, and parsed resume only.

        Raises:
            NotFoundError: If the application is missing or belongs to someone else.
        """

        candidate = await self.get_owned(candidate_id, user_id)
        return await self.to_application_read(candidate)

    async def to_application_read(self, candidate: Candidate) -> CandidateApplicationRead:
        """Build the candidate-facing application payload.

        Args:
            candidate: The application row.

        Returns:
            A payload without notes, scores, or matcher explanations.
        """

        job_title = None
        if self._job_repo is not None:
            job = await self._job_repo.get_by_id(candidate.job_id)
            job_title = None if job is None else job.title
        return CandidateApplicationRead(
            id=candidate.id,
            job_id=candidate.job_id,
            job_title=job_title,
            status=candidate.status,
            parsed_profile=candidate.parsed_profile,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
        )

    async def update_own_profile(
        self, candidate_id: uuid.UUID, user_id: uuid.UUID, data: CandidateProfileUpdate
    ) -> Candidate:
        """Let a candidate correct their own parsed resume fields.

        Args:
            candidate_id: The application to correct.
            user_id: The candidate account.
            data: Fields to replace.

        Returns:
            The updated candidate.

        Raises:
            NotFoundError: If the application is missing or belongs to someone else.
            ValidationAppError: If the resume has not been parsed yet.
        """

        await self.get_owned(candidate_id, user_id)
        return await self.update_profile(candidate_id, data)

    async def get_assessment(self, candidate_id: uuid.UUID) -> AssessmentRead:
        """Load the latest stored score and matcher explanation.

        Args:
            candidate_id: The candidate to read.

        Returns:
            The assessment payload.

        Raises:
            NotFoundError: If the candidate does not exist, or has not been scored.
        """

        candidate = await self.get_candidate(candidate_id)
        if self._score_repo is None:
            raise NotFoundError("Assessment not available.")
        score = await self._score_repo.get_latest_for_candidate(candidate_id)
        if score is None:
            raise NotFoundError("Assessment not available.")

        matching = candidate.matching_result or {}
        return AssessmentRead(
            candidate_id=candidate.id,
            total_score=score.total_score,
            skills_score=score.skills_score,
            experience_score=score.experience_score,
            projects_score=score.projects_score,
            education_score=score.education_score,
            certifications_score=score.certifications_score,
            reasoning=score.reasoning,
            match_percentage=matching.get("match_percentage", candidate.match_percentage),
            missing_skills=list(matching.get("missing_skills") or []),
            extra_skills=list(matching.get("extra_skills") or []),
            experience_comparison=matching.get("experience_comparison"),
            explanation=matching.get("explanation"),
            score_overridden=bool(candidate.score_overridden),
        )

    async def change_status(
        self, candidate_id: uuid.UUID, new_status: CandidateStatus, actor_id: uuid.UUID
    ) -> Candidate:
        """Move a candidate to a new pipeline status and record the change.

        Args:
            candidate_id: The candidate to update.
            new_status: The requested status.
            actor_id: The staff user making the change.

        Returns:
            The updated candidate.

        Raises:
            NotFoundError: If the candidate does not exist.
            ValidationAppError: If the transition is not allowed.
        """

        candidate = await self.get_candidate(candidate_id)
        assert_transition(candidate.status, new_status)
        previous = candidate.status
        candidate.status = new_status
        await self._require_event_repo().add(
            CandidateStatusEvent(
                candidate_id=candidate.id,
                actor_id=actor_id,
                from_status=previous,
                to_status=new_status,
            )
        )
        return candidate

    async def add_note(self, candidate_id: uuid.UUID, author_id: uuid.UUID, body: str) -> CandidateNote:
        """Attach a private note to a candidate.

        Args:
            candidate_id: The candidate the note is about.
            author_id: The staff user writing the note.
            body: Note text.

        Returns:
            The saved note.

        Raises:
            NotFoundError: If the candidate does not exist.
        """

        await self.get_candidate(candidate_id)
        return await self._require_note_repo().add(
            CandidateNote(candidate_id=candidate_id, author_id=author_id, body=body)
        )

    async def list_notes(self, candidate_id: uuid.UUID) -> list[CandidateNoteRead]:
        """List private notes for a candidate, newest first.

        Args:
            candidate_id: The candidate whose notes to list.

        Returns:
            Note records. These are not included on the public candidate payload.

        Raises:
            NotFoundError: If the candidate does not exist.
        """

        await self.get_candidate(candidate_id)
        notes = await self._require_note_repo().list_for_candidate(candidate_id)
        return [CandidateNoteRead.model_validate(note) for note in notes]

    async def list_events(self, candidate_id: uuid.UUID) -> list[CandidateStatusEventRead]:
        """List status changes for a candidate, oldest first.

        Args:
            candidate_id: The candidate whose history to list.

        Returns:
            Audit events.

        Raises:
            NotFoundError: If the candidate does not exist.
        """

        await self.get_candidate(candidate_id)
        events = await self._require_event_repo().list_for_candidate(candidate_id)
        return [CandidateStatusEventRead.model_validate(event) for event in events]

    async def update_profile(self, candidate_id: uuid.UUID, data: CandidateProfileUpdate) -> Candidate:
        """Correct parsed profile fields and drop the stale match explanation.

        Args:
            candidate_id: The candidate to correct.
            data: Fields to replace. Omitted fields stay as they are.

        Returns:
            The updated candidate. `matching_result` is cleared so the
            caller must run the hiring workflow again.

        Raises:
            NotFoundError: If the candidate does not exist.
            ValidationAppError: If the resume has not been parsed yet.
        """

        candidate = await self.get_candidate(candidate_id)
        if candidate.parsed_profile is None:
            raise ValidationAppError("Candidate has not been parsed yet.")

        profile = dict(candidate.parsed_profile)
        profile.update(data.model_dump(exclude_unset=True))
        candidate.parsed_profile = profile
        candidate.matching_result = None
        return candidate

    async def override_score(
        self, candidate_id: uuid.UUID, total_score: float, reason: str, actor_id: uuid.UUID
    ) -> Candidate:
        """Replace the latest total score with a recruiter's value.

        Args:
            candidate_id: The candidate whose score to override.
            total_score: The replacement total, from 0 to 100.
            reason: Why the score was changed. Stored as a private note.
            actor_id: The staff user making the override.

        Returns:
            The updated candidate.

        Raises:
            NotFoundError: If the candidate or a score does not exist.
        """

        candidate = await self.get_candidate(candidate_id)
        if self._score_repo is None:
            raise NotFoundError("Assessment not available.")
        score = await self._score_repo.get_latest_for_candidate(candidate_id)
        if score is None:
            raise NotFoundError("Assessment not available.")

        score.total_score = total_score
        candidate.score_overridden = True
        await self._require_note_repo().add(
            CandidateNote(
                candidate_id=candidate.id,
                author_id=actor_id,
                body=f"Score overridden to {total_score:g}: {reason}",
            )
        )
        return candidate

    def _require_note_repo(self) -> CandidateNoteRepository:
        """Return the note repository or fail closed if it was not injected."""

        if self._note_repo is None:
            raise NotFoundError("Notes are not available.")
        return self._note_repo

    def _require_event_repo(self) -> CandidateStatusEventRepository:
        """Return the event repository or fail closed if it was not injected."""

        if self._event_repo is None:
            raise NotFoundError("Status history is not available.")
        return self._event_repo
