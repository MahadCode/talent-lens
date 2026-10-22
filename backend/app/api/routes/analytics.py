"""Recruitment analytics endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.core.dependencies import get_analytics_service, require_hr
from app.schemas.analytics import AnalyticsSummary, JobAnalytics
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"], dependencies=[Depends(require_hr())])


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
    summary="Dashboard summary",
    description="Live counts of open jobs, applications, shortlists, pending reviews, and upcoming interviews.",
)
async def analytics_summary(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummary:
    """Return the recruiter dashboard counts.

    Args:
        analytics_service: Injected `AnalyticsService`.

    Returns:
        The summary counts.
    """

    return await analytics_service.summary()


@router.get(
    "/jobs/{job_id}",
    response_model=JobAnalytics,
    summary="Analytics for one job",
    responses={404: {"description": "Job not found."}},
)
async def job_analytics(
    job_id: uuid.UUID, analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> JobAnalytics:
    """Return stage counts, shortlist rate, processing time, and skill gaps.

    Args:
        job_id: The job to report on.
        analytics_service: Injected `AnalyticsService`.

    Returns:
        The job analytics payload.
    """

    return await analytics_service.job_report(job_id)
