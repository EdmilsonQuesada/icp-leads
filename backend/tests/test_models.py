import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.base import Base
from app.models.lead import Lead, LeadStatus, LeadCategory, LeadPlatform
from app.models.lead_event import LeadEvent
from app.models.search_job import SearchJob

DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)

def test_create_lead(db):
    lead = Lead(
        username="maria_silva",
        platform=LeadPlatform.INSTAGRAM,
        display_name="Maria Silva",
        score=0,
        category=LeadCategory.FRIO,
        status=LeadStatus.MONITORING,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    assert lead.id is not None
    assert lead.username == "maria_silva"

def test_lead_event(db):
    lead = Lead(username="joao", platform=LeadPlatform.YOUTUBE,
                score=50, category=LeadCategory.MORNO,
                status=LeadStatus.MONITORING)
    db.add(lead)
    db.commit()
    event = LeadEvent(lead_id=lead.id, event_type="comment",
                      description="Comentou em post de constelação",
                      score_delta=5, score_after=55)
    db.add(event)
    db.commit()
    assert event.id is not None
    assert event.lead_id == lead.id

def test_search_job(db):
    job = SearchJob(
        keywords=["constelação familiar"],
        platforms=["instagram"],
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    assert job.id is not None
    assert job.keywords == ["constelação familiar"]
