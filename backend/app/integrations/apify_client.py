"""
Wrapper around Apify SDK for Instagram scraping
"""
import logging
from typing import Optional, List, Dict, Any
from apify_client import ApifyClient as ApifySDK
from app.core.config import settings

logger = logging.getLogger(__name__)

INSTAGRAM_HASHTAG_SCRAPER = "apify/instagram-hashtag-scraper"


class ApifyClient:
    """Wrapper for Apify SDK - Provides high-level methods for Instagram scraping"""

    def __init__(self):
        if not settings.APIFY_API_TOKEN:
            raise ValueError("APIFY_API_TOKEN not configured in .env")
        self.client = ApifySDK(settings.APIFY_API_TOKEN)
        self.logger = logger

    def scrape_hashtags(
        self,
        hashtags: List[str],
        max_posts_per_hashtag: int = 50,
        search_posts: bool = True,
    ) -> Dict[str, Any]:
        """
        Scrape posts from Instagram hashtags

        Args:
            hashtags: List of hashtags (with or without #)
            max_posts_per_hashtag: Maximum posts to collect per hashtag
            search_posts: Whether to search posts (vs reels)

        Returns:
            Dict with run_id, dataset_id, and status
        """
        clean_hashtags = [h.lstrip("#") for h in hashtags]

        run_input = {
            "hashtags": clean_hashtags,
            "searchPostsFirst": search_posts,
            "postsPerHashtag": max_posts_per_hashtag,
        }

        self.logger.info(f"🚀 Starting Apify run for hashtags: {clean_hashtags}")

        try:
            actor_run = self.client.actor(INSTAGRAM_HASHTAG_SCRAPER).call(
                run_input=run_input
            )

            result = {
                "run_id": actor_run["id"],
                "dataset_id": actor_run["defaultDatasetId"],
                "status": actor_run["status"],
            }

            self.logger.info(f"✅ Actor run created: {result['run_id']}")
            return result

        except Exception as e:
            self.logger.error(f"❌ Error starting Apify run: {e}")
            raise

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get status of a running actor"""
        try:
            run = self.client.run(run_id).get()
            return {
                "run_id": run["id"],
                "status": run["status"],
                "created": run["createdAt"],
                "started": run.get("startedAt"),
                "finished": run.get("finishedAt"),
            }
        except Exception as e:
            self.logger.error(f"Error getting run status: {e}")
            raise

    def fetch_results(self, dataset_id: str) -> List[Dict[str, Any]]:
        """Fetch results from a completed actor run"""
        try:
            dataset = self.client.dataset(dataset_id)
            items = dataset.list_items().items
            self.logger.info(f"📊 Fetched {len(items)} items from dataset")
            return items
        except Exception as e:
            self.logger.error(f"Error fetching results: {e}")
            raise
