import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.search_job import SearchJob
from app.schemas.lead import SearchJobCreate
from app.integrations.apify_client import ApifyClient
from app.tasks.apify_import import import_apify_results

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
def search_instagram_apify(
    request: SearchJobCreate,
    db: Session = Depends(get_db),
):
    """
    Start Instagram search using Apify (new, reliable method)
    Input: {"keywords": ["constelacao"], "platforms": ["instagram"]}
    """
    try:
        logger.info(f"🚀 Starting Apify search with keywords: {request.keywords}")

        # Initialize Apify client
        apify = ApifyClient()
        logger.info("✅ ApifyClient initialized")

        # Start Apify run
        logger.info("→ Calling apify.scrape_hashtags...")
        run_result = apify.scrape_hashtags(
            hashtags=request.keywords,
            max_posts_per_hashtag=50,
        )
        logger.info(f"✅ Apify run started: {run_result['run_id']}")

        # Store run info in database for tracking
        logger.info("→ Creating SearchJob...")
        search_job = SearchJob(
            keywords=request.keywords,
            platforms=request.platforms,
            status="running"
        )
        db.add(search_job)
        db.commit()
        logger.info(f"✅ SearchJob created with ID: {search_job.id}")

        # Queue import task (temporarily commented out for testing)
        # logger.info("→ Queuing import task...")
        # import_apify_results.apply_async(
        #     kwargs={
        #         "dataset_id": run_result["dataset_id"],
        #         "search_job_id": search_job.id,
        #     },
        #     countdown=15
        # )
        logger.info("✅ SearchJob ready for import (manual trigger needed)")

        return {
            "job_id": search_job.id,
            "status": "running",
            "message": "Apify scraping started"
        }

    except Exception as e:
        logger.error(f"❌ Error starting Apify search: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")
