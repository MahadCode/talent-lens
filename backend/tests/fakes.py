"""In-memory repositories for service tests. They do not open a database."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.core.constants import CandidateStatus
from app.models.candidate import Candidate


def stamp(entity):
    """Assign an id and timestamps the way a database flush would."""

    if getattr(entity, "id", None) is None:
        entity.id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    if getattr(entity, "created_at", None) is None:
        entity.created_at = now
    if getattr(entity, "updated_at", None) is None:
        entity.updated_at = now
    return entity


class MemoryCandidateRepo:
    """Stores `Candidate` rows in a dict."""

    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, Candidate] = {}

    async def get_by_id(self, entity_id: uuid.UUID) -> Candidate | None:
        return self.rows.get(entity_id)

    async def add(self, entity: Candidate) -> Candidate:
        stamp(entity)
        self.rows[entity.id] = entity
        return entity

    async def get_by_user_and_job(self, user_id, job_id):
        for row in self.rows.values():
            if row.user_id == user_id and row.job_id == job_id:
                return row
        return None

    async def list_by_user(self, user_id):
        matches = [row for row in self.rows.values() if row.user_id == user_id]
        return sorted(matches, key=lambda row: row.created_at, reverse=True)

    async def count(self, status: CandidateStatus | None = None, job_id: uuid.UUID | None = None) -> int:
        rows = list(self.rows.values())
        if status is not None:
            rows = [row for row in rows if row.status == status]
        if job_id is not None:
            rows = [row for row in rows if row.job_id == job_id]
        return len(rows)

    async def status_counts_for_job(self, job_id: uuid.UUID) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in self.rows.values():
            if row.job_id != job_id:
                continue
            counts[row.status.value] = counts.get(row.status.value, 0) + 1
        return counts

    async def list_matching_results(self, job_id: uuid.UUID) -> list[dict | None]:
        return [row.matching_result for row in self.rows.values() if row.job_id == job_id]


class MemoryScoreRepo:
    """Stores `Score` rows and returns the newest one for a candidate."""

    def __init__(self) -> None:
        self.rows: list = []

    async def add(self, entity):
        stamp(entity)
        self.rows.append(entity)
        return entity

    async def get_latest_for_candidate(self, candidate_id: uuid.UUID):
        matches = [row for row in self.rows if row.candidate_id == candidate_id]
        if not matches:
            return None
        return max(matches, key=lambda row: row.created_at)


class MemoryNoteRepo:
    """Stores private notes, newest first on read."""

    def __init__(self) -> None:
        self.rows: list = []

    async def add(self, entity):
        stamp(entity)
        self.rows.append(entity)
        return entity

    async def list_for_candidate(self, candidate_id: uuid.UUID):
        matches = [row for row in self.rows if row.candidate_id == candidate_id]
        return sorted(matches, key=lambda row: row.created_at, reverse=True)


class MemoryEventRepo:
    """Stores status events and can measure time spent in PARSED."""

    def __init__(self, candidates: MemoryCandidateRepo) -> None:
        self.rows: list = []
        self._candidates = candidates

    async def add(self, entity):
        stamp(entity)
        self.rows.append(entity)
        return entity

    async def list_for_candidate(self, candidate_id: uuid.UUID):
        matches = [row for row in self.rows if row.candidate_id == candidate_id]
        return sorted(matches, key=lambda row: row.created_at)

    async def processing_samples(self, job_id: uuid.UUID):
        samples = []
        for candidate in self.candidates_for(job_id):
            exits = [
                event.created_at
                for event in self.rows
                if event.candidate_id == candidate.id and event.from_status == CandidateStatus.PARSED
            ]
            left_at = min(exits) if exits else None
            samples.append((candidate.created_at, left_at))
        return samples

    def candidates_for(self, job_id: uuid.UUID):
        return [row for row in self._candidates.rows.values() if row.job_id == job_id]


class MemoryJobRepo:
    """Stores `Job` rows."""

    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, object] = {}

    async def get_by_id(self, entity_id: uuid.UUID):
        return self.rows.get(entity_id)

    async def add(self, entity):
        stamp(entity)
        self.rows[entity.id] = entity
        return entity

    async def count_by_status(self, status) -> int:
        return sum(1 for row in self.rows.values() if row.status == status)

    async def list_by_status(self, status=None, offset: int = 0, limit: int = 100):
        rows = list(self.rows.values())
        if status is not None:
            rows = [row for row in rows if row.status == status]
        return rows[offset : offset + limit]


class MemoryResumeRepo:
    """Stores uploaded resume rows."""

    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, object] = {}

    async def add(self, entity):
        stamp(entity)
        self.rows[entity.id] = entity
        return entity

    async def get_latest_for_candidate(self, candidate_id: uuid.UUID):
        matches = [row for row in self.rows.values() if row.candidate_id == candidate_id]
        if not matches:
            return None
        return max(matches, key=lambda row: row.created_at)


class MemoryInterviewRepo:
    """Stores AI interview rows, including question JSON."""

    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, object] = {}

    async def add(self, entity):
        stamp(entity)
        self.rows[entity.id] = entity
        return entity

    async def get_question_bank(self, candidate_id: uuid.UUID):
        matches = [
            row
            for row in self.rows.values()
            if row.candidate_id == candidate_id and row.questions is not None
        ]
        if not matches:
            return None
        return max(matches, key=lambda row: row.created_at)

    async def find_by_question_id(self, question_id: str):
        for row in self.rows.values():
            for item in row.questions or []:
                if item.get("id") == question_id:
                    return row
        return None


class MemoryScheduleRepo:
    """Stores booked interviews and applies the 60-minute conflict rule."""

    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, object] = {}

    async def get_by_id(self, entity_id: uuid.UUID):
        return self.rows.get(entity_id)

    async def add(self, entity):
        stamp(entity)
        self.rows[entity.id] = entity
        return entity

    async def find_conflict(self, interviewer_name: str, scheduled_at: datetime):
        window = timedelta(minutes=60)
        for row in self.rows.values():
            same_person = row.interviewer_name.strip().casefold() == interviewer_name
            if same_person and abs(row.scheduled_at - scheduled_at) <= window:
                return row
        return None

    async def list_filtered(self, starts=None, ends=None, candidate_id=None):
        rows = list(self.rows.values())
        if starts is not None:
            rows = [row for row in rows if row.scheduled_at >= starts]
        if ends is not None:
            rows = [row for row in rows if row.scheduled_at <= ends]
        if candidate_id is not None:
            rows = [row for row in rows if row.candidate_id == candidate_id]
        return sorted(rows, key=lambda row: row.scheduled_at)

    async def count_upcoming(self, now: datetime) -> int:
        return sum(1 for row in self.rows.values() if row.scheduled_at > now)
