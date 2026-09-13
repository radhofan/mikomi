from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), index=True, default="", nullable=False)
    job_title: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    company_name: Mapped[str] = mapped_column(String(100), index=True, default="", nullable=False)
    email: Mapped[str] = mapped_column(String(100), index=True, default="", nullable=False)
    phone_number: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    phone_digits: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, default=0)
    country: Mapped[str] = mapped_column(String(100), index=True, default="Unknown", nullable=False)
    city: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lead_status: Mapped[str] = mapped_column(String(100), index=True, default="New", nullable=False)
    lifecycle_stage: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    original_source: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    contact_owner: Mapped[str] = mapped_column(String(100), index=True, default="Unassigned", nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_detail: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
