import pytest
from app.services.scorer import LeadScorer, ScoreResult

def test_score_zero_for_empty_lead():
    scorer = LeadScorer()
    result = scorer.score({
        "bio": "",
        "country": "US",
        "is_business": True,
        "followers": 500000,
        "engagement_events": [],
        "comments": [],
    })
    assert result.total < 25
    assert result.category == "descarte"

def test_score_high_for_ideal_lead():
    scorer = LeadScorer()
    result = scorer.score({
        "bio": "buscando cura e autoconhecimento terapia 🌿",
        "country": "BR",
        "is_business": False,
        "followers": 800,
        "engagement_events": [
            {"type": "like", "context": "constelação familiar"},
            {"type": "comment", "context": "constelação sistêmica"},
            {"type": "like", "context": "constelação familiar"},
        ],
        "comments": [
            {"text": "quero fazer sessão de constelação, como funciona?"},
        ],
    })
    assert result.total >= 75
    assert result.category == "quente"

def test_intention_keyword_detected():
    scorer = LeadScorer()
    result = scorer.score({
        "bio": "",
        "country": "BR",
        "is_business": False,
        "followers": 500,
        "engagement_events": [],
        "comments": [{"text": "preciso de ajuda, quero marcar uma sessão"}],
    })
    assert result.intention_score > 0

def test_category_quente():
    scorer = LeadScorer()
    assert scorer._classify(85) == "quente"
    assert scorer._classify(75) == "quente"

def test_category_morno():
    scorer = LeadScorer()
    assert scorer._classify(74) == "morno"
    assert scorer._classify(50) == "morno"

def test_category_frio():
    scorer = LeadScorer()
    assert scorer._classify(49) == "frio"
    assert scorer._classify(25) == "frio"

def test_category_descarte():
    scorer = LeadScorer()
    assert scorer._classify(24) == "descarte"
    assert scorer._classify(0) == "descarte"

def test_br_location_bonus():
    scorer = LeadScorer()
    br_result = scorer.score({
        "bio": "", "country": "BR", "is_business": False,
        "followers": 500, "engagement_events": [], "comments": [],
    })
    us_result = scorer.score({
        "bio": "", "country": "US", "is_business": False,
        "followers": 500, "engagement_events": [], "comments": [],
    })
    assert br_result.profile_score > us_result.profile_score

def test_spiritual_bio_bonus():
    scorer = LeadScorer()
    result = scorer.score({
        "bio": "amo terapia e constelação familiar",
        "country": "BR", "is_business": False,
        "followers": 500, "engagement_events": [], "comments": [],
    })
    assert result.profile_score > 10

def test_score_result_fields():
    scorer = LeadScorer()
    result = scorer.score({
        "bio": "", "country": "BR", "is_business": False,
        "followers": 500, "engagement_events": [], "comments": [],
    })
    assert hasattr(result, "engagement_score")
    assert hasattr(result, "intention_score")
    assert hasattr(result, "profile_score")
    assert hasattr(result, "total")
    assert hasattr(result, "category")
    assert result.total == result.engagement_score + result.intention_score + result.profile_score
