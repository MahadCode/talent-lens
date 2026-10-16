"""Allowed candidate status transitions for human pipeline actions."""

from __future__ import annotations

from app.core.constants import CandidateStatus
from app.exceptions.errors import ValidationAppError

ALLOWED_TRANSITIONS: dict[CandidateStatus, frozenset[CandidateStatus]] = {
    CandidateStatus.PARSED: frozenset({CandidateStatus.SHORTLISTED, CandidateStatus.REJECTED}),
    CandidateStatus.MANUAL_REVIEW: frozenset({CandidateStatus.SHORTLISTED, CandidateStatus.REJECTED}),
    CandidateStatus.SHORTLISTED: frozenset({CandidateStatus.INTERVIEWING, CandidateStatus.REJECTED}),
    CandidateStatus.INTERVIEWING: frozenset({CandidateStatus.HIRED, CandidateStatus.NOT_HIRED}),
}


def assert_transition(current: CandidateStatus, target: CandidateStatus) -> None:
    """Reject a status change that the pipeline does not allow.

    Args:
        current: The candidate's status before the change.
        target: The requested status.

    Raises:
        ValidationAppError: If `target` is not a legal next status.
    """

    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValidationAppError(f"Cannot move a candidate from {current.value} to {target.value}.")
