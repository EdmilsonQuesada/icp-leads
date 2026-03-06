import pytest
from app.collectors.linkedin import LinkedInEnricher

def test_extract_city_with_country():
    enricher = LinkedInEnricher.__new__(LinkedInEnricher)
    result = enricher._extract_city("São Paulo, Brasil")
    assert result == "São Paulo"

def test_extract_city_without_country():
    enricher = LinkedInEnricher.__new__(LinkedInEnricher)
    result = enricher._extract_city("Rio de Janeiro")
    assert result == "Rio de Janeiro"

def test_extract_city_none():
    enricher = LinkedInEnricher.__new__(LinkedInEnricher)
    result = enricher._extract_city(None)
    assert result is None

def test_extract_city_empty():
    enricher = LinkedInEnricher.__new__(LinkedInEnricher)
    result = enricher._extract_city("")
    assert result is None

def test_estimate_age_from_graduation():
    enricher = LinkedInEnricher.__new__(LinkedInEnricher)
    import datetime
    current_year = datetime.datetime.now().year
    age = enricher._estimate_age_from_graduation_year(current_year - 10)
    # Formou há 10 anos + 22 anos na formatura = ~32 anos
    assert 28 <= age <= 36

def test_enrich_returns_dict_without_credentials():
    """Sem credenciais, retorna dict vazio mas não explode"""
    import asyncio
    from unittest.mock import patch
    enricher = LinkedInEnricher()
    # Patch settings para simular sem credenciais
    with patch("app.collectors.linkedin.settings") as mock_settings:
        mock_settings.LINKEDIN_EMAIL = ""
        result = asyncio.run(enricher.enrich("João Silva"))
    assert isinstance(result, dict)
    assert "city" in result
    assert "source" in result
    assert result["source"] == "linkedin"
