import logging
from googleapiclient.discovery import build
from app.core.config import settings

logger = logging.getLogger(__name__)

class YouTubeCollector:
    def __init__(self):
        self.service = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)

    def search_videos(self, query: str, max_results: int = 50) -> list[dict]:
        response = self.service.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results,
            relevanceLanguage="pt",
            regionCode="BR",
        ).execute()

        return [
            {
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel_title": item["snippet"]["channelTitle"],
                "channel_id": item["snippet"]["channelId"],
                "published_at": item["snippet"]["publishedAt"],
            }
            for item in response.get("items", [])
        ]

    def get_comments(self, video_id: str, max_results: int = 100) -> list[dict]:
        comments = []
        page_token = None

        while len(comments) < max_results:
            params = dict(
                videoId=video_id,
                part="snippet",
                maxResults=min(100, max_results - len(comments)),
                textFormat="plainText",
            )
            if page_token:
                params["pageToken"] = page_token

            response = self.service.commentThreads().list(**params).execute()

            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "username": snippet["authorDisplayName"],
                    "channel_id": snippet.get("authorChannelId", {}).get("value"),
                    "text": snippet["textDisplay"],
                    "likes": snippet.get("likeCount", 0),
                    "published_at": snippet["publishedAt"],
                })

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return comments
