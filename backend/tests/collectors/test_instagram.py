import pytest
from unittest.mock import MagicMock, patch
from app.collectors.instagram import InstagramCollector

@pytest.fixture
def mock_client():
    with patch("app.collectors.instagram.Client") as MockClient:
        instance = MockClient.return_value
        instance.user_info_by_username.return_value = MagicMock(
            pk=123456,
            username="maria_silva",
            full_name="Maria Silva",
            biography="Amo constelação familiar 🌿",
            follower_count=843,
            following_count=612,
            is_business=False,
            profile_pic_url="https://example.com/pic.jpg",
        )
        instance.hashtag_medias_recent.return_value = [
            MagicMock(
                pk=789,
                code="abc123",
                user=MagicMock(username="maria_silva"),
                caption_text="Amei minha sessão de constelação #constelaçãofamiliar",
                like_count=45,
                comment_count=8,
            )
        ]
        instance.media_comments.return_value = [
            MagicMock(
                user=MagicMock(username="joao_paz"),
                text="Como faço para agendar uma sessão?",
                created_at_utc=None,
            )
        ]
        yield instance

def test_get_profile(mock_client):
    collector = InstagramCollector.__new__(InstagramCollector)
    collector.client = mock_client
    profile = collector.get_profile("maria_silva")
    assert profile["username"] == "maria_silva"
    assert profile["followers"] == 843
    assert "constelação" in profile["bio"]
    assert profile["platform"] == "instagram"

def test_search_hashtag(mock_client):
    collector = InstagramCollector.__new__(InstagramCollector)
    collector.client = mock_client
    posts = collector.search_hashtag("constelaçãofamiliar", limit=5)
    assert len(posts) >= 1
    assert posts[0]["username"] == "maria_silva"
    assert "constelação" in posts[0]["post_text"]

def test_get_comments(mock_client):
    collector = InstagramCollector.__new__(InstagramCollector)
    collector.client = mock_client
    comments = collector.get_comments("789", limit=10)
    assert len(comments) == 1
    assert comments[0]["username"] == "joao_paz"
    assert "sessão" in comments[0]["text"]
