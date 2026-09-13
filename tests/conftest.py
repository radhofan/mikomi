import pytest
from fastapi.testclient import TestClient

from api.database import SessionLocal
from api.main import app
from ai_assisted_mini_lead_management_system.db.models import Lead


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.query(Lead).filter(Lead.email.like("%@testdomain.com")).delete(synchronize_session=False)
        session.commit()
        session.close()
