import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.base import Base
from app.models.lead import Lead, LeadPlatform, LeadCategory, LeadStatus
from app.models.lead_event import LeadEvent
from app.db.session import get_db

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def override_get_db():
    with Session(engine) as session:
        yield session

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    app.dependency_overrides.pop(get_db, None)

client = TestClient(app)

def _create_lead(db, username="test_user", category=LeadCategory.QUENTE, score=80):
    lead = Lead(
        username=username,
        platform=LeadPlatform.INSTAGRAM,
        score=score,
        category=category,
        status=LeadStatus.MONITORING,
        display_name="Test User",
        city="São Paulo",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

def test_list_leads_empty():
    response = client.get("/leads")
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []

def test_list_leads_with_data():
    with Session(engine) as db:
        _create_lead(db)
    response = client.get("/leads")
    assert response.status_code == 200
    assert response.json()["total"] == 1

def test_filter_by_category_quente():
    with Session(engine) as db:
        _create_lead(db, username="quente", category=LeadCategory.QUENTE, score=80)
        _create_lead(db, username="frio", category=LeadCategory.FRIO, score=20)
    response = client.get("/leads?category=quente")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["username"] == "quente"

def test_filter_by_platform():
    with Session(engine) as db:
        _create_lead(db)
    response = client.get("/leads?platform=instagram")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/leads?platform=youtube")
    assert response.status_code == 200
    assert response.json()["total"] == 0

def test_get_lead_by_id():
    with Session(engine) as db:
        lead = _create_lead(db)
        lead_id = lead.id
    response = client.get(f"/leads/{lead_id}")
    assert response.status_code == 200
    assert response.json()["username"] == "test_user"
    assert response.json()["city"] == "São Paulo"

def test_get_lead_not_found():
    response = client.get("/leads/99999")
    assert response.status_code == 404

def test_mark_as_contacted():
    with Session(engine) as db:
        lead = _create_lead(db)
        lead_id = lead.id
    response = client.patch(f"/leads/{lead_id}/contacted")
    assert response.status_code == 200
    assert response.json()["status"] == "contacted"
    assert response.json()["contacted_at"] is not None

def test_archive_lead():
    with Session(engine) as db:
        lead = _create_lead(db)
        lead_id = lead.id
    response = client.delete(f"/leads/{lead_id}")
    assert response.status_code == 200
    # Verifica que está arquivado
    with Session(engine) as db:
        lead = db.get(Lead, lead_id)
        assert lead.status == LeadStatus.ARCHIVED

def test_leads_sorted_by_score_desc():
    with Session(engine) as db:
        _create_lead(db, username="low", score=20, category=LeadCategory.FRIO)
        _create_lead(db, username="high", score=90, category=LeadCategory.QUENTE)
    response = client.get("/leads")
    items = response.json()["items"]
    assert items[0]["username"] == "high"
    assert items[1]["username"] == "low"

def test_get_lead_events():
    with Session(engine) as db:
        lead = _create_lead(db)
        event = LeadEvent(
            lead_id=lead.id,
            event_type="comment",
            description="Comentou em post de constelação",
            score_delta=5,
            score_after=85,
        )
        db.add(event)
        db.commit()
        lead_id = lead.id
    response = client.get(f"/leads/{lead_id}/events")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["event_type"] == "comment"
