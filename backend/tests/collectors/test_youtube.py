import pytest
from unittest.mock import MagicMock, patch
from app.collectors.youtube import YouTubeCollector

@pytest.fixture
def mock_youtube():
    with patch("app.collectors.youtube.build") as mock_build:
        service = MagicMock()
        mock_build.return_value = service

        # Mock search
        service.search.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": {"videoId": "abc123"},
                    "snippet": {
                        "title": "Constelação Familiar - Como funciona",
                        "channelTitle": "Canal Espiritualidade",
                        "channelId": "UC123",
                        "publishedAt": "2024-01-01T00:00:00Z",
                    }
                }
            ]
        }

        # Mock comments
        service.commentThreads.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "João Paz",
                                "authorChannelId": {"value": "UC456"},
                                "textDisplay": "Quero fazer uma sessão, como faço?",
                                "likeCount": 3,
                                "publishedAt": "2024-01-02T00:00:00Z",
                            }
                        }
                    }
                }
            ],
            "nextPageToken": None,
        }
        yield service

def test_search_videos(mock_youtube):
    collector = YouTubeCollector.__new__(YouTubeCollector)
    collector.service = mock_youtube
    videos = collector.search_videos("constelação familiar", max_results=5)
    assert len(videos) == 1
    assert videos[0]["video_id"] == "abc123"
    assert "Constelação" in videos[0]["title"]
    assert videos[0]["channel_title"] == "Canal Espiritualidade"

def test_get_comments(mock_youtube):
    collector = YouTubeCollector.__new__(YouTubeCollector)
    collector.service = mock_youtube
    comments = collector.get_comments("abc123", max_results=10)
    assert len(comments) == 1
    assert "Quero fazer" in comments[0]["text"]
    assert comments[0]["username"] == "João Paz"
    assert comments[0]["likes"] == 3
