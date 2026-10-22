"""Decision Agent.

Applies deterministic business rules to a candidate's total score to reach
a hiring decision. This agent intentionally does NOT call an LLM: the
business rules are simple, auditable thresholds, and keeping them
deterministic avoids non-reproducible hiring decisions.
"""

from __future__ import annotations

from ai_agents.config.settings import Settings, get_settings
from ai_agents.utils.schemas import DecisionResult, DecisionType, ScoringResult


class DecisionAgent:
    """Maps a candidate's total score to a `DecisionResult` via fixed thresholds."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the agent.

        Args:
            settings: Optional settings override, primarily for testing
                different threshold configurations. Defaults to the shared
                application settings.
        """

        self._settings = settings or get_settings()

    def run(self, score_result: ScoringResult) -> DecisionResult:
        """Determine the hiring decision for a scored candidate.

        Business rules:
            - total_score >= shortlist_score_threshold -> SHORTLIST
            - manual_review_score_threshold <= total_score < shortlist_score_threshold -> MANUAL_REVIEW
            - total_score < manual_review_score_threshold -> REJECT

        Args:
            score_result: The candidate's scoring result.

        Returns:
            A `DecisionResult` containing the decision and its rationale.
        """

        total = score_result.total_score
        shortlist_threshold = self._settings.shortlist_score_threshold
        review_threshold = self._settings.manual_review_score_threshold

        if total >= shortlist_threshold:
            decision = DecisionType.SHORTLIST
            reason = (
                f"Total score {total:.1f} meets the shortlist threshold of "
                f"{shortlist_threshold:.1f}. {score_result.reasoning}"
            )
        elif total >= review_threshold:
            decision = DecisionType.MANUAL_REVIEW
            reason = (
                f"Total score {total:.1f} falls between the manual review threshold "
                f"({review_threshold:.1f}) and the shortlist threshold "
                f"({shortlist_threshold:.1f}). {score_result.reasoning}"
            )
        else:
            decision = DecisionType.REJECT
            reason = (
                f"Total score {total:.1f} is below the manual review threshold of "
                f"{review_threshold:.1f}. {score_result.reasoning}"
            )

        return DecisionResult(decision=decision, reason=reason)
