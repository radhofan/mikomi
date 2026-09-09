import os
from pathlib import Path

import alembic.command
import alembic.config
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJ_ROOT = Path(__file__).resolve().parents[2]


def regenerate_database() -> None:
    load_dotenv(PROJ_ROOT / ".env")

    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/leads")

    if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
        rel_path = db_url.replace("sqlite:///", "")
        resolved_db_url = f"sqlite:///{(PROJ_ROOT / rel_path).resolve()}"
    else:
        resolved_db_url = db_url

    print(f"[INFO] Connecting to target database: {resolved_db_url}")
    engine = create_engine(resolved_db_url, isolation_level="AUTOCOMMIT")

    with engine.connect() as connection:
        if "postgresql" in resolved_db_url:
            print("[INFO] Dropping and recreating PostgreSQL public schema...")
            connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
            connection.execute(text("CREATE SCHEMA public;"))
            connection.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
            connection.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        elif "sqlite" in resolved_db_url:
            print("[INFO] Dropping existing SQLite tables...")
            connection.execute(text("PRAGMA foreign_keys = OFF;"))
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"))
            for (table_name,) in result.fetchall():
                connection.execute(text(f'DROP TABLE IF EXISTS "{table_name}";'))
            connection.execute(text("PRAGMA foreign_keys = ON;"))

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
