import pytest
from datetime import date
from app.collectors.facebook import FacebookEnricher

def test_parse_birthdate_numeric():
    enricher = FacebookEnricher.__new__(FacebookEnricher)
    result = enricher._parse_birthdate("15/03/1990")
    assert result is not None
    assert result.day == 15
    assert result.month == 3
    assert result.year == 1990

def test_parse_birthdate_portuguese():
    enricher = FacebookEnricher.__new__(FacebookEnricher)
    result = enricher._parse_birthdate("15 de março de 1990")
    assert result is not None
    assert result.day == 15
    assert result.month == 3
    assert result.year == 1990

def test_parse_birthdate_with_dash():
    enricher = FacebookEnricher.__new__(FacebookEnricher)
    result = enricher._parse_birthdate("15-03-1990")
    assert result is not None
    assert result.year == 1990

def test_parse_birthdate_invalid():
    enricher = FacebookEnricher.__new__(FacebookEnricher)
    result = enricher._parse_birthdate("texto sem data")
    assert result is None

def test_parse_birthdate_empty():
    enricher = FacebookEnricher.__new__(FacebookEnricher)
    result = enricher._parse_birthdate("")
    assert result is None

def test_parse_all_months():
    enricher = FacebookEnricher.__new__(FacebookEnricher)
    months = [
        ("janeiro", 1), ("fevereiro", 2), ("março", 3), ("abril", 4),
        ("maio", 5), ("junho", 6), ("julho", 7), ("agosto", 8),
        ("setembro", 9), ("outubro", 10), ("novembro", 11), ("dezembro", 12),
    ]
    for month_name, month_num in months:
        result = enricher._parse_birthdate(f"10 de {month_name} de 2000")
        assert result is not None, f"Falhou para {month_name}"
        assert result.month == month_num
