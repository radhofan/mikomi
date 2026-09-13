import os
from pathlib import Path

import alembic.command
import alembic.config
from dotenv import load_dotenv
import pandas as pd
from pgserver.postgres_server import get_server
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ai_assisted_mini_lead_management_system.db.models import Lead

PROJ_ROOT = Path(__file__).resolve().parents[2]


def get_db_url() -> str:
    load_dotenv(PROJ_ROOT / ".env")
    env_url = os.getenv("DATABASE_URL")
    if env_url and not env_url.startswith("postgresql+psycopg2://postgres:postgres@localhost:5432"):
        return env_url

    pgdata = PROJ_ROOT / "pgdata"
    srv = get_server(pgdata)
    res = srv.psql("SELECT 1 FROM pg_database WHERE datname = 'leads';")
    if "1" not in res:
        srv.psql("CREATE DATABASE leads;")
    return srv.get_uri("leads")


def seed_database(db_url: str) -> None:
    csv_path = PROJ_ROOT / "data" / "interim" / "leads_cleaned.csv"
    if not csv_path.exists():
        print(f"[WARN] Cleaned CSV not found at {csv_path}")
        return

    print(f"[INFO] Seeding database from {csv_path}...")
    df = pd.read_csv(csv_path)

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")

    df["phone_digits"] = df["phone_digits"].fillna(0).astype(int)
    for col in [
        "first_name",
        "last_name",
        "full_name",
        "job_title",
        "company_name",
        "email",
        "phone_number",
        "country",
        "lead_status",
        "lifecycle_stage",
        "original_source",
        "contact_owner",
        "notes",
    ]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "record_id": int(row["record_id"]),
                "first_name": row.get("first_name", ""),
                "last_name": row.get("last_name", ""),
                "full_name": row.get("full_name", ""),
                "job_title": row.get("job_title", ""),
                "company_name": row.get("company_name", ""),
                "email": row.get("email", ""),
                "phone_number": row.get("phone_number", ""),
                "phone_digits": int(row["phone_digits"]),
                "country": row.get("country", "") or "Unknown",
                "city": float(row["city"]) if pd.notna(row.get("city")) else None,
                "lead_status": row.get("lead_status", "") or "New",
                "lifecycle_stage": row.get("lifecycle_stage", ""),
                "original_source": row.get("original_source", ""),
                "contact_owner": row.get("contact_owner", "") or "Unassigned",
                "created_at": row["created_at"].to_pydatetime() if pd.notna(row["created_at"]) else None,
                "updated_at": row["updated_at"].to_pydatetime() if pd.notna(row["updated_at"]) else None,
                "notes": row.get("notes", ""),
                "source_channel": None,
                "source_detail": None,
            }
        )

    engine = create_engine(db_url)
    with Session(engine) as session:
        session.bulk_insert_mappings(Lead, records)
        session.commit()
    engine.dispose()

    print(f"[INFO] Successfully inserted {len(records)} leads into database.")


def regenerate_database() -> None:
    resolved_db_url = get_db_url()

    print(f"[INFO] Connecting to target database: {resolved_db_url}")
    engine = create_engine(resolved_db_url, isolation_level="AUTOCOMMIT")

    with engine.connect() as connection:
        print("[INFO] Dropping and recreating PostgreSQL public schema...")
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        connection.execute(text("CREATE SCHEMA public;"))
        connection.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        connection.execute(text("GRANT ALL ON SCHEMA public TO public;"))

    engine.dispose()

    alembic_ini_path = PROJ_ROOT / "alembic.ini"
    alembic_cfg = alembic.config.Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(PROJ_ROOT / "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", resolved_db_url)

    print("[INFO] Applying Alembic migrations up to head...")
    alembic.command.upgrade(alembic_cfg, "head")
    print("[INFO] Database schema successfully regenerated.")

    seed_database(resolved_db_url)


if __name__ == "__main__":
    regenerate_database()
