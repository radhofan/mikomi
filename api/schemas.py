"""
API schemas for request validation and response serialization.

Note: Update if database columns in models.py change.
"""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_id: int
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    job_title: str = ""
    company_name: str = ""
    email: str = ""
    phone_number: str = ""
    phone_digits: int = 0
    country: str = "Unknown"
    city: Optional[float] = None
    lead_status: str = "New"
    lifecycle_stage: str = ""
    original_source: str = ""
    contact_owner: str = "Unassigned"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    notes: str = ""
    source_channel: Optional[str] = None
    source_detail: Optional[str] = None


class LeadUpdate(BaseModel):
    lead_status: Optional[str] = None
    contact_owner: Optional[str] = None
    notes: Optional[str] = None


class LeadIngestRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = ""
    company: Optional[str] = ""
    country: Optional[str] = ""
    message: Optional[str] = ""
    form_id: Optional[str] = None
    form_name: Optional[str] = None
    page_url: Optional[str] = None
    submitted_at: Optional[datetime] = None


class IngestResult(BaseModel):
    action: str
    lead: LeadResponse


class DashboardResponse(BaseModel):
    total_leads: int
    by_status: Dict[str, int]
    by_source_channel: Dict[str, int]
