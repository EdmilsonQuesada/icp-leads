import time
import random
import logging
import os
from instagrapi import Client
from app.core.config import settings

logger = logging.getLogger(__name__)

SESSION_PATH = "/app/instagram_session.json"


class InstagramCollector:
    def __init__(self):
        self.client = Client()
        self._login()

    def _login(self):
        if not os.path.exists(SESSION_PATH):
            raise RuntimeError(
                "Sessão do Instagram não encontrada. "
                "Execute: docker compose exec -it backend python scripts/instagram_login.py"
            )
        try:
            self.client.load_settings(SESSION_PATH)
            self.client.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
            logger.info("Instagram login bem-sucedido via sessão salva")
        except Exception as e:
            logger.error(f"Falha no login Instagram: {e}")
            raise

    def _delay(self):
        time.sleep(random.uniform(4, 10))

    def get_profile(self, username: str) -> dict:
        self._delay()
        user = self.client.user_info_by_username(username)
        return {
            "username": user.username,
            "display_name": user.full_name,
            "bio": user.biography,
            "followers": user.follower_count,
            "following": user.following_count,
            "is_business": user.is_business,
            "avatar_url": str(user.profile_pic_url),
            "platform": "instagram",
        }

    def search_hashtag(self, hashtag: str, limit: int = 38) -> list[dict]:
        self._delay()
        medias = self.client.hashtag_medias_recent(hashtag, amount=limit)
        results = []
        for media in medias:
            results.append({
                "username": media.user.username,
                "post_text": media.caption_text or "",
                "likes": media.like_count,
                "comments_count": media.comment_count,
                "post_url": f"https://instagram.com/p/{media.code}",
            })
            self._delay()
        return results

    def get_comments(self, media_id: str, limit: int = 75) -> list[dict]:
        self._delay()
        comments = self.client.media_comments(media_id, amount=limit)
        return [
            {
                "username": c.user.username,
                "text": c.text,
                "created_at": c.created_at_utc.isoformat() if c.created_at_utc else None,
            }
            for c in comments
        ]
