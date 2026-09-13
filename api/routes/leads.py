import csv
from datetime import datetime
import io
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ai_assisted_mini_lead_management_system.db.models import Lead
from api.database import get_db
from api.routes.utils import apply_lead_filters, process_single_ingest
from api.schemas import IngestResult, LeadIngestRequest, LeadResponse, LeadUpdate

router = APIRouter(prefix="/leads", tags=["leads"])


# GET /leads
@router.get("", response_model=List[LeadResponse])
def list_leads(
    response: Response,
    status: Optional[str] = Query(None, description="Filter by lead status"),
    owner: Optional[str] = Query(None, description="Filter by contact owner"),
    country: Optional[str] = Query(None, description="Filter by country"),
    q: Optional[str] = Query(None, description="Search across name, company, and email"),
    limit: int = Query(50, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db),
):
    """
    GET /leads

    List leads with optional filtering and pagination.

    Params:
        status (Optional[str]): Filter by lead_status.
        owner (Optional[str]): Filter by contact_owner.
        country (Optional[str]): Filter by country.
        q (Optional[str]): Free-text search across name, company, and email.
        limit (int): Maximum number of records to return (default 50).
        offset (int): Number of records to skip (default 0).
        db (Session): Database session dependency.

    Returns:
        List[LeadResponse]: List of matched lead records.
    """
    query = db.query(Lead)
    query = apply_lead_filters(query, status=status, owner=owner, country=country, q=q)
    total_count = query.count()
    response.headers["X-Total-Count"] = str(total_count)
    return query.order_by(Lead.id.asc()).offset(offset).limit(limit).all()


# GET /leads/export
@router.get("/export")
def export_leads(
    status: Optional[str] = Query(None, description="Filter by lead status"),
    owner: Optional[str] = Query(None, description="Filter by contact owner"),
    country: Optional[str] = Query(None, description="Filter by country"),
    q: Optional[str] = Query(None, description="Search across name, company, and email"),
    db: Session = Depends(get_db),
):
    """
    GET /leads/export

    Export current filtered leads view as a CSV download.

    Params:
        status (Optional[str]): Filter by lead_status.
        owner (Optional[str]): Filter by contact_owner.
        country (Optional[str]): Filter by country.
        q (Optional[str]): Free-text search across name, company, and email.
        db (Session): Database session dependency.

    Returns:
        Response: Streaming CSV file attachment (leads_export.csv).
    """
    query = db.query(Lead)
    query = apply_lead_filters(query, status=status, owner=owner, country=country, q=q)
    leads = query.order_by(Lead.id.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "id",
        "record_id",
        "first_name",
        "last_name",
        "full_name",
        "job_title",
        "company_name",
        "email",
        "phone_number",
        "phone_digits",
        "country",
        "lead_status",
        "lifecycle_stage",
        "original_source",
        "contact_owner",
        "source_channel",
        "source_detail",
        "created_at",
        "updated_at",
        "notes",
    ]
    writer.writerow(headers)

    for lead in leads:
        writer.writerow(
            [
                lead.id,
                lead.record_id,
                lead.first_name,
                lead.last_name,
                lead.full_name,
                lead.job_title,
                lead.company_name,
                lead.email,
                lead.phone_number,
                lead.phone_digits,
                lead.country,
                lead.lead_status,
                lead.lifecycle_stage,
                lead.original_source,
                lead.contact_owner,
                lead.source_channel or "",
                lead.source_detail or "",
                lead.created_at.isoformat() if lead.created_at else "",
                lead.updated_at.isoformat() if lead.updated_at else "",
                lead.notes,
            ]
        )

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


# GET /leads/{id}
@router.get("/{id}", response_model=LeadResponse)
def get_lead(id: int, db: Session = Depends(get_db)):
    """
    GET /leads/{id}

    Retrieve a single lead by its primary key ID.

    Params:
        id (int): Primary key ID of the lead.
        db (Session): Database session dependency.

    Returns:
        LeadResponse: Full lead record details.

    Raises:
        HTTPException(404): If lead is not found.
    """
    lead = db.query(Lead).filter(Lead.id == id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


# PATCH /leads/{id}
@router.patch("/{id}", response_model=LeadResponse)
def update_lead(id: int, payload: LeadUpdate, db: Session = Depends(get_db)):
    """
    PATCH /leads/{id}

    Update lead status, contact owner, or notes.

    Params:
        id (int): Primary key ID of the lead.
        payload (LeadUpdate): Fields to update:
            - lead_status (Optional[str])
            - contact_owner (Optional[str])
            - notes (Optional[str])
        db (Session): Database session dependency.

    Returns:
        LeadResponse: Updated lead record.

    Raises:
        HTTPException(404): If lead is not found.
    """
    lead = db.query(Lead).filter(Lead.id == id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if payload.lead_status is not None:
        lead.lead_status = payload.lead_status
    if payload.contact_owner is not None:
        lead.contact_owner = payload.contact_owner
    if payload.notes is not None:
        lead.notes = payload.notes

    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return lead


# POST /leads/ingest
@router.post("/ingest", response_model=Union[IngestResult, List[IngestResult]])
def ingest_lead(
    payload: Union[LeadIngestRequest, List[LeadIngestRequest]],
    db: Session = Depends(get_db),
):
    """
    POST /leads/ingest

    Ingest website form submissions (single or batch).
    Matches existing leads to deduplicate or creates a new lead.

    Params:
        payload (Union[LeadIngestRequest, List[LeadIngestRequest]]): Single or batch website form submission payloads.
        db (Session): Database session dependency.

    Returns:
        Union[IngestResult, List[IngestResult]]: Ingest result containing action and lead data.
    """
    if isinstance(payload, list):
        return [process_single_ingest(item, db) for item in payload]
    return process_single_ingest(payload, db)
