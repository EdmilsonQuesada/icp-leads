from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.settings import AppSettings

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsUpdate(BaseModel):
    keywords: list[str] | None = None
    monitor_days_quente: int | None = None
    monitor_days_morno: int | None = None
    monitor_days_frio: int | None = None
    max_leads_per_day: int | None = None
    collect_hour: int | None = None
    instagram_enabled: bool | None = None
    youtube_enabled: bool | None = None
    facebook_enrichment: bool | None = None
    linkedin_enrichment: bool | None = None

def _get_or_create(db: Session) -> AppSettings:
    s = db.get(AppSettings, 1)
    if not s:
        s = AppSettings(id=1)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s

@router.get("")
def get_settings(db: Session = Depends(get_db)):
    s = _get_or_create(db)
    return {
        "keywords": s.keywords,
        "monitor_days_quente": s.monitor_days_quente,
        "monitor_days_morno": s.monitor_days_morno,
        "monitor_days_frio": s.monitor_days_frio,
        "max_leads_per_day": s.max_leads_per_day,
        "collect_hour": s.collect_hour,
        "instagram_enabled": s.instagram_enabled,
        "youtube_enabled": s.youtube_enabled,
        "facebook_enrichment": s.facebook_enrichment,
        "linkedin_enrichment": s.linkedin_enrichment,
    }

@router.patch("")
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    s = _get_or_create(db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return get_settings(db)
