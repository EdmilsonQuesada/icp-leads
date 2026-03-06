from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.lead_event import LeadEvent

router = APIRouter(prefix="/leads", tags=["events"])

@router.get("/{lead_id}/events")
def get_lead_events(lead_id: int, db: Session = Depends(get_db)):
    events = (
        db.query(LeadEvent)
        .filter(LeadEvent.lead_id == lead_id)
        .order_by(LeadEvent.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "description": e.description,
            "score_delta": e.score_delta,
            "score_after": e.score_after,
            "created_at": str(e.created_at),
        }
        for e in events
    ]
