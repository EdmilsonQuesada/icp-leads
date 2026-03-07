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

        # Process each post
        for post in items:
            try:
                # Extract post's author/creator username from the post data
                # Note: Apify hashtag scraper may not always have owner data for free tier
                # We'll work with what we have: extract from mentions if available

                post_id = post.get("id") or post.get("shortCode")
                caption = post.get("caption", "")
                post_url = post.get("url", "")

                # Try to extract username from caption mentions or hashtags
                # For now, we'll focus on comment authors since they're more explicit

                # Process comments (extract commenters as leads)
                comments = post.get("latestComments", [])
                if not comments and "comments" in post:
                    comments = post.get("comments", [])

                for comment in comments:
                    try:
                        commenter = comment.get("owner", {}) if isinstance(comment, dict) else {}
                        username = commenter.get("username") if isinstance(commenter, dict) else None

                        if not username:
                            # Try alternative field names
                            username = comment.get("username") if isinstance(comment, dict) else None

                        if username:
                            lead_data = {
                                "username": username,
                                "display_name": commenter.get("name") if isinstance(commenter, dict) else None,
                                "followers": commenter.get("followers") if isinstance(commenter, dict) else None,
                                "profile_url": f"https://instagram.com/{username}",
                                "bio": comment.get("text") if isinstance(comment, dict) else str(comment),
                                "country": "BR",
                                "is_business_account": False,
                            }

                            # Enrich data (gender, score, categorization)
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
                            else:
                                skipped_count += 1

                    except Exception as e:
                        logger.warning(f"Error processing comment: {e}")
                        continue

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
