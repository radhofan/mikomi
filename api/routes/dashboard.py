from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ai_assisted_mini_lead_management_system.db.models import Lead
from api.database import get_db
from api.schemas import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# GET /dashboard
@router.get("", response_model=DashboardResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    GET /dashboard

    Returns lead counts aggregated by lead_status and by source_channel.

    Params:
        db (Session): Database session dependency.

    Returns:
        DashboardResponse:
            - total_leads (int): Total count of leads in database.
            - by_status (dict[str, int]): Counts grouped by lead_status.
            - by_source_channel (dict[str, int]): Counts grouped by source_channel.
    """
    total_leads = db.query(func.count(Lead.id)).scalar() or 0

    status_counts = (
        db.query(Lead.lead_status, func.count(Lead.id))
        .group_by(Lead.lead_status)
        .all()
    )
    by_status = {
        (status if status else "Unknown"): count
        for status, count in status_counts
    }

    channel_counts = (
        db.query(Lead.source_channel, func.count(Lead.id))
        .group_by(Lead.source_channel)
        .all()
    )
    by_source_channel = {
        (channel if channel else "Unassigned"): count
        for channel, count in channel_counts
    }

    return DashboardResponse(
        total_leads=total_leads,
        by_status=by_status,
        by_source_channel=by_source_channel,
    )
