from datetime import datetime
import re
from typing import Optional

import pandas as pd
from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session

from ai_assisted_mini_lead_management_system.db.models import Lead
from api.schemas import IngestResult, LeadIngestRequest, LeadResponse


def apply_lead_filters(
    query: Query,
    status: Optional[str] = None,
    owner: Optional[str] = None,
    country: Optional[str] = None,
    q: Optional[str] = None,
) -> Query:
    """
    Helper function to apply common filtering logic across queries.

    Params:
        query (Query): Base SQLAlchemy query.
        status (Optional[str]): Filter by lead_status (case-insensitive).
        owner (Optional[str]): Filter by contact_owner (case-insensitive).
        country (Optional[str]): Filter by country (case-insensitive).
        q (Optional[str]): Free-text search matching full_name, company_name, or email.

    Returns:
        Query: SQLAlchemy query with filters applied.
    """
    if status:
        query = query.filter(Lead.lead_status.ilike(status))
    if owner:
        query = query.filter(Lead.contact_owner.ilike(owner))
    if country:
        query = query.filter(Lead.country.ilike(country))
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Lead.full_name.ilike(term),
                Lead.company_name.ilike(term),
                Lead.email.ilike(term),
            )
        )
    return query


def process_single_ingest(submission: LeadIngestRequest, db: Session) -> IngestResult:
    """
    Helper function to ingest a single website form submission with deduplication.

    Matches existing leads on normalized email, then falls back to normalized phone digits.
    Updates existing record if matched, or creates a new lead if not found.

    Params:
        submission (LeadIngestRequest): Website form submission data.
        db (Session): Database session dependency.

    Returns:
        IngestResult: Action ('created' or 'updated') and the resulting LeadResponse.
    """
    clean_email = submission.email.strip().lower()
    digits_raw = re.sub(r"\D", "", submission.phone or "")
    phone_digits = int(digits_raw) if digits_raw else 0

    existing = db.query(Lead).filter(func.lower(Lead.email) == clean_email).first()

    if not existing and phone_digits > 0:
        existing = db.query(Lead).filter(Lead.phone_digits == phone_digits).first()

    if existing:
        if submission.message:
            existing.notes = (
                f"{existing.notes}\nWebsite Form: {submission.message}".strip()
                if existing.notes
                else f"Website Form: {submission.message}"
            )
        if not existing.company_name and submission.company:
            existing.company_name = submission.company
        if (not existing.country or existing.country == "Unknown") and submission.country:
            existing.country = submission.country

        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return IngestResult(
            action="updated",
            lead=LeadResponse.model_validate(existing),
        )

    name_parts = submission.name.strip().split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    max_record_id = db.query(func.max(Lead.record_id)).scalar()
    next_record_id = (max_record_id + 1) if max_record_id else 100000001

    created_at = submission.submitted_at or datetime.utcnow()

    details = [part for part in [submission.form_name, submission.page_url] if part]
    source_detail = " - ".join(details) if details else "Website Ingest"

    new_lead = Lead(
        record_id=next_record_id,
        first_name=first_name,
        last_name=last_name,
        full_name=submission.name.strip(),
        job_title="",
        company_name=submission.company or "",
        email=clean_email,
        phone_number=submission.phone or "",
        phone_digits=phone_digits,
        country=submission.country or "Unknown",
        lead_status="New",
        lifecycle_stage="Lead",
        original_source="Website Form",
        contact_owner="Unassigned",
        created_at=created_at,
        updated_at=created_at,
        notes=submission.message or "",
        source_channel="Website",
        source_detail=source_detail,
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return IngestResult(
        action="created",
        lead=LeadResponse.model_validate(new_lead),
    )


def load_lead_dataframe(db: Session) -> pd.DataFrame:
    """
    Helper function to load leads from PostgreSQL into a DataFrame for record linkage.
    """
    leads = db.query(Lead).all()
    if not leads:
        return pd.DataFrame()

    records = [
        {
            "record_id": lead.record_id,
            "full_name": lead.full_name or "",
            "company_name": lead.company_name or "",
            "email": lead.email or "",
            "phone_digits_str": str(lead.phone_digits) if lead.phone_digits else "",
            "email_domain": lead.email.split("@")[-1] if lead.email and "@" in lead.email else "",
        }
        for lead in leads
    ]
    return pd.DataFrame(records)

