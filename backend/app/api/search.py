from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.search_job import SearchJob
from app.schemas.lead import SearchJobCreate

router = APIRouter(prefix="/search", tags=["search"])

@router.post("")
def create_search_job(payload: SearchJobCreate, db: Session = Depends(get_db)):
    job = SearchJob(keywords=payload.keywords, platforms=payload.platforms)
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"job_id": job.id, "status": "queued"}

@router.get("")
def list_search_jobs(db: Session = Depends(get_db)):
    jobs = db.query(SearchJob).order_by(SearchJob.created_at.desc()).limit(20).all()
    return [
        {
            "id": j.id,
            "keywords": j.keywords,
            "platforms": j.platforms,
            "status": j.status,
            "leads_found": j.leads_found,
            "created_at": str(j.created_at),
        }
        for j in jobs
    ]
