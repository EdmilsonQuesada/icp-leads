from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from datetime import datetime
from app.db.session import get_db
from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadOut, LeadList

router = APIRouter(prefix="/leads", tags=["leads"])

@router.get("/cities")
def list_cities(db: Session = Depends(get_db)):
    """Retorna lista de cidades distintas que têm ao menos um lead."""
    rows = (
        db.query(distinct(Lead.city))
        .filter(Lead.city.isnot(None), Lead.city != "")
        .order_by(Lead.city)
        .all()
    )
    return [r[0] for r in rows]

@router.get("", response_model=LeadList)
def list_leads(
    category: str | None = None,
    platform: str | None = None,
    status: str | None = None,
    city: str | None = None,
    gender: str | None = None,
    birthday_soon: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Lead)
    if category:
        query = query.filter(Lead.category == category)
    if platform:
        query = query.filter(Lead.platform == platform)
    if status:
        query = query.filter(Lead.status == status)
    if city:
        query = query.filter(Lead.city.ilike(f"%{city}%"))
    if gender:
        query = query.filter(Lead.gender == gender)
    if birthday_soon:
        from datetime import date, timedelta
        today = date.today()
        query = query.filter(Lead.birthdate.isnot(None))
    total = query.count()
    items = query.order_by(Lead.score.desc()).offset(skip).limit(limit).all()
    return LeadList(total=total, items=items)

@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return lead

@router.patch("/{lead_id}/contacted", response_model=LeadOut)
def mark_contacted(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    lead.status = LeadStatus.CONTACTED
    lead.contacted_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return lead

@router.delete("/{lead_id}")
def archive_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    lead.status = LeadStatus.ARCHIVED
    db.commit()
    return {"ok": True}
