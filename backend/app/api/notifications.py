from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from app.db.session import get_db
from app.models.lead import Lead, LeadCategory, LeadStatus

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("")
def get_notifications(db: Session = Depends(get_db)):
    notifications = []

    quentes = db.query(Lead).filter(
        Lead.category == LeadCategory.QUENTE,
        Lead.status == LeadStatus.MONITORING,
    ).count()
    if quentes:
        notifications.append({
            "type": "hot_leads",
            "message": f"🔥 {quentes} lead(s) quente(s) prontos para contato",
            "priority": "high",
        })

    today = date.today()
    birthday_leads = db.query(Lead).filter(Lead.birthdate.isnot(None)).all()
    birthday_count = 0
    for lead in birthday_leads:
        try:
            bday = lead.birthdate.replace(year=today.year)
            if 0 <= (bday - today).days <= 7:
                birthday_count += 1
        except ValueError:
            pass
    if birthday_count:
        notifications.append({
            "type": "birthday",
            "message": f"🎂 {birthday_count} lead(s) com aniversário nos próximos 7 dias",
            "priority": "medium",
        })

    return notifications
