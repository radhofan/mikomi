"""migration 20260909155712

Revision ID: 20260909155712
Revises: 
Create Date: 2026-09-09 15:57:12.744128

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260909155712"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('record_id', sa.BigInteger(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('last_name', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('full_name', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('job_title', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('company_name', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('email', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('phone_number', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('phone_digits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('country', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('city', sa.Float(), nullable=True),
        sa.Column('lead_status', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('lifecycle_stage', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('original_source', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('contact_owner', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=False, server_default=''),
        sa.Column('source_channel', sa.String(length=50), nullable=True),
        sa.Column('source_detail', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_leads_record_id', 'leads', ['record_id'], unique=True)
    op.create_index('ix_leads_full_name', 'leads', ['full_name'], unique=False)
    op.create_index('ix_leads_company_name', 'leads', ['company_name'], unique=False)
    op.create_index('ix_leads_email', 'leads', ['email'], unique=False)
    op.create_index('ix_leads_phone_digits', 'leads', ['phone_digits'], unique=False)
    op.create_index('ix_leads_country', 'leads', ['country'], unique=False)
    op.create_index('ix_leads_lead_status', 'leads', ['lead_status'], unique=False)
    op.create_index('ix_leads_contact_owner', 'leads', ['contact_owner'], unique=False)
    op.create_index('ix_leads_created_at', 'leads', ['created_at'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_leads_created_at', table_name='leads')
    op.drop_index('ix_leads_contact_owner', table_name='leads')
    op.drop_index('ix_leads_lead_status', table_name='leads')
    op.drop_index('ix_leads_country', table_name='leads')
    op.drop_index('ix_leads_phone_digits', table_name='leads')
    op.drop_index('ix_leads_email', table_name='leads')
    op.drop_index('ix_leads_company_name', table_name='leads')
    op.drop_index('ix_leads_full_name', table_name='leads')
    op.drop_index('ix_leads_record_id', table_name='leads')
    op.drop_table("leads")
