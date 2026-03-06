import pytest
from unittest.mock import patch, MagicMock
from app.collectors.transcriber import VideoTranscriber

def test_skip_short_videos():
    """Vídeos < 10 min não precisam de transcrição"""
    transcriber = VideoTranscriber()
    assert transcriber.should_transcribe(duration_seconds=300) is False
    assert transcriber.should_transcribe(duration_seconds=599) is False

def test_transcribe_long_videos():
    """Vídeos >= 10 min devem ser transcritos"""
    transcriber = VideoTranscriber()
    assert transcriber.should_transcribe(duration_seconds=600) is True
    assert transcriber.should_transcribe(duration_seconds=3600) is True

def test_get_transcript_returns_none_for_short_video():
    """get_transcript retorna None para vídeos curtos"""
    mock_info = {"duration": 300, "automatic_captions": {}, "subtitles": {}}
    with patch("app.collectors.transcriber.yt_dlp.YoutubeDL") as MockYDL:
        instance = MockYDL.return_value.__enter__.return_value
        instance.extract_info.return_value = mock_info
        transcriber = VideoTranscriber()
        result = transcriber.get_transcript("short_video_id")
        assert result is None

def test_get_transcript_returns_string_for_long_video_with_captions():
    """get_transcript retorna string para vídeos com legendas automáticas"""
    mock_info = {
        "duration": 3600,
        "automatic_captions": {
            "pt": [{"url": "https://example.com/captions.vtt", "ext": "vtt"}]
        },
        "subtitles": {},
    }
    with patch("app.collectors.transcriber.yt_dlp.YoutubeDL") as MockYDL:
        instance = MockYDL.return_value.__enter__.return_value
        instance.extract_info.return_value = mock_info
        transcriber = VideoTranscriber()
        result = transcriber.get_transcript("long_video_id")
        assert result is not None
        assert isinstance(result, str)
