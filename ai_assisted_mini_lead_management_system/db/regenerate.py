import os
from pathlib import Path

import alembic.command
import alembic.config
from dotenv import load_dotenv
from pgserver.postgres_server import get_server
from sqlalchemy import create_engine, text

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
    print("[INFO] Database successfully regenerated to latest migration.")


if __name__ == "__main__":
    regenerate_database()
