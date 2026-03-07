"""
Celery task to import data from Apify and create leads
"""
import logging
from typing import List, Dict, Any
from celery import shared_task
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.integrations.apify_client import ApifyClient
from app.models.lead import Lead, LeadStatus, LeadCategory, LeadPlatform
from app.services.scorer import LeadScorer

logger = logging.getLogger(__name__)


def enrich_lead_data(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich lead data with scoring information

    Args:
        lead_data: Dictionary with basic lead information

    Returns:
        Dictionary with enriched data including scores and category
    """
    scorer = LeadScorer()

    # Prepare data for scoring
    score_input = {
        "bio": lead_data.get("bio") or "",
        "country": lead_data.get("country", "BR"),
        "is_business": lead_data.get("is_business_account", False),
        "followers": lead_data.get("followers") or 0,
        "engagement_events": [],
        "comments": [{"text": lead_data.get("bio", "")}] if lead_data.get("bio") else [],
    }

    # Get score result
    result = scorer.score(score_input)

    # Check if comment text is negative
    if lead_data.get("bio") and scorer._is_negative(lead_data.get("bio", "")):
        status = LeadStatus.ARCHIVED
        category = LeadCategory.DESCARTE
        score = 0
        score_engagement = 0
        score_intention = 0
        score_profile = 0
    else:
        status = LeadStatus.PENDING
        category = LeadCategory(result.category)
        score = result.total
        score_engagement = result.engagement_score
        score_intention = result.intention_score
        score_profile = result.profile_score

    # Return enriched lead data
    return {
        "username": lead_data["username"],
        "platform": LeadPlatform.INSTAGRAM,
        "display_name": lead_data.get("display_name"),
        "bio": lead_data.get("bio"),
        "profile_url": lead_data.get("profile_url"),
        "avatar_url": lead_data.get("avatar_url"),
        "followers": lead_data.get("followers"),
        "following": lead_data.get("following"),
        "is_business_account": lead_data.get("is_business_account", False),
        "country": lead_data.get("country", "BR"),
        "score": score,
        "score_engagement": score_engagement,
        "score_intention": score_intention,
        "score_profile": score_profile,
        "category": category,
        "status": status,
    }


@shared_task(bind=True, max_retries=3)
def import_apify_results(self, dataset_id: str, search_job_id: int) -> Dict[str, Any]:
    """
    Import results from completed Apify run and create leads

    Args:
        dataset_id: Apify dataset ID
        search_job_id: SearchJob ID in our database
    """
    db = SessionLocal()

    try:
        apify = ApifyClient()

        logger.info(f"📥 Importing Apify dataset: {dataset_id}")

        # Fetch all results from Apify
        items = apify.fetch_results(dataset_id)

        if not items:
            logger.warning(f"No items found in dataset {dataset_id}")
            return {"imported": 0, "skipped": 0}

        logger.info(f"📊 Processing {len(items)} items from Apify")

        imported_count = 0
        skipped_count = 0

        # Process each post - extract post AUTHORS as leads
        for post in items:
            try:
                # Extract post author (ownerUsername is always available)
                username = post.get("ownerUsername")
                if not username:
                    skipped_count += 1
                    continue

                # Build lead data from post author
                lead_data = {
                    "username": username,
                    "display_name": post.get("ownerFullName"),
                    "profile_url": f"https://instagram.com/{username}",
                    "bio": (post.get("caption") or "")[:500],  # Use caption as context
                    "country": "BR",
                    "is_business_account": False,
                }

                # Enrich data (score, categorization)
                enriched = enrich_lead_data(lead_data)

                # Check if lead already exists
                existing = db.query(Lead).filter(
                    Lead.username == enriched["username"],
                    Lead.platform == LeadPlatform.INSTAGRAM
                ).first()

                if not existing:
                    lead = Lead(**enriched)
                    db.add(lead)
                    imported_count += 1
                    logger.info(f"   + Lead: @{username}")
                else:
                    skipped_count += 1

                # Also process latestComments if available (paid plans)
                comments = post.get("latestComments") or []
                for comment in comments:
                    if not isinstance(comment, dict):
                        continue
                    commenter = comment.get("ownerUsername") or comment.get("owner", {}).get("username")
                    if commenter:
                        c_lead_data = {
                            "username": commenter,
                            "display_name": comment.get("ownerFullName"),
                            "profile_url": f"https://instagram.com/{commenter}",
                            "bio": (comment.get("text") or "")[:500],
                            "country": "BR",
                            "is_business_account": False,
                        }
                        c_enriched = enrich_lead_data(c_lead_data)
                        c_existing = db.query(Lead).filter(
                            Lead.username == c_enriched["username"],
                            Lead.platform == LeadPlatform.INSTAGRAM
                        ).first()
                        if not c_existing:
                            db.add(Lead(**c_enriched))
                            imported_count += 1

            except Exception as e:
                logger.error(f"Error processing post {post.get('id')}: {e}")
                skipped_count += 1
                continue

        db.commit()
        logger.info(f"✅ Import complete: {imported_count} new, {skipped_count} skipped")

        return {
            "imported": imported_count,
            "skipped": skipped_count,
            "dataset_id": dataset_id,
        }

    except Exception as e:
        logger.error(f"❌ Error importing Apify results: {e}")
        db.rollback()
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

    finally:
        db.close()
