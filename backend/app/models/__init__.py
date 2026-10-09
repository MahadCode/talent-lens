"""Import all ORM models so `Base.metadata` is fully populated.

Alembic's `env.py` imports this module (indirectly, via `app.database.base`)
before calling `autogenerate` so every table is known to SQLAlchemy's
metadata, regardless of which individual model modules a given script
happens to import directly.
"""

from __future__ import annotations

from app.models.candidate import Candidate
from app.models.candidate_note import CandidateNote
from app.models.candidate_status_event import CandidateStatusEvent
from app.models.email_challenge import EmailChallenge
from app.models.email_log import EmailLog
from app.models.interview import Interview
from app.models.job import Job
from app.models.refresh_token import RefreshToken
from app.models.resume import Resume
from app.models.scheduled_interview import ScheduledInterview
from app.models.score import Score
from app.models.user import User

__all__ = [
    "Candidate",
    "CandidateNote",
    "CandidateStatusEvent",
    "EmailChallenge",
    "EmailLog",
    "Interview",
    "Job",
    "RefreshToken",
    "Resume",
    "ScheduledInterview",
    "Score",
    "User",
]
