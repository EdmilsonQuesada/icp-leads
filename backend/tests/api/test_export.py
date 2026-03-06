import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session
from app.main import app
from app.db.base import Base
from app.models.lead import Lead, LeadPlatform, LeadCategory, LeadStatus
from app.db.session import get_db

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)

def override_get_db():
    with Session(engine) as session:
        yield session

@pytest.fixture(autouse=True)
def setup_db():
    # Registra o override específico deste módulo antes de cada teste
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        lead = Lead(
            username="export_user", platform=LeadPlatform.INSTAGRAM,
            score=70, category=LeadCategory.MORNO, status=LeadStatus.MONITORING,
            display_name="Export User", city="São Paulo"
        )
        db.add(lead)
        db.commit()
    yield
    Base.metadata.drop_all(engine)
    app.dependency_overrides.pop(get_db, None)

client = TestClient(app)

def test_export_csv():
    response = client.get("/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert b"export_user" in response.content

def test_export_excel():
    response = client.get("/export/excel")
    assert response.status_code == 200
    assert "spreadsheet" in response.headers["content-type"] or "excel" in response.headers["content-type"]
    assert len(response.content) > 0
