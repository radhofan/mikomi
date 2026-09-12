import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from pgserver.postgres_server import get_server
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

PROJ_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJ_ROOT / ".env")


def get_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url and not env_url.startswith("postgresql+psycopg2://postgres:postgres@localhost:5432"):
        return env_url

    pgdata = PROJ_ROOT / "pgdata"
    srv = get_server(pgdata)
    res = srv.psql("SELECT 1 FROM pg_database WHERE datname = 'leads';")
    if "1" not in res:
        srv.psql("CREATE DATABASE leads;")
    return srv.get_uri("leads")


engine = create_engine(get_database_url(), echo=False)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
