import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.search_job import SearchJob
from app.schemas.lead import SearchJobCreate
from app.integrations.apify_client import ApifyClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

@router.post("")
def create_search_job(payload: SearchJobCreate, db: Session = Depends(get_db)):
    job = SearchJob(keywords=payload.keywords, platforms=payload.platforms)
    db.add(job)
    db.commit()
    db.refresh(job)

    from app.tasks.search import run_search_job
    run_search_job.delay(job.id)

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

@router.post("/apify")
async def search_instagram_apify(
    request: SearchJobCreate,
    db: Session = Depends(get_db),
):
    """
    Start Instagram search using Apify (new, reliable method)

    Input: {"hashtags": ["constelacao"], "platforms": ["instagram"], "max_posts": 50}
    """
    try:
        apify = ApifyClient()

        # Start Apify run
        run_result = apify.scrape_hashtags(
            hashtags=request.keywords,
            max_posts_per_hashtag=50,
        )

        # Store run info in database for tracking
        search_job = SearchJob(
            job_id=run_result["run_id"],
            keywords=request.keywords,
            platforms=request.platforms,
            status="running",
            metadata={
                "apify_run_id": run_result["run_id"],
                "apify_dataset_id": run_result["dataset_id"],
                "source": "apify"
            }
        )
        db.add(search_job)
        db.commit()

        return {
            "job_id": search_job.id,
            "status": "running",
            "message": "Apify scraping started"
        }

    except Exception as e:
        logger.error(f"Error starting Apify search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
