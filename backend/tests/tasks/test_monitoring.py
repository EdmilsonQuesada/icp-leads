import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from app.tasks.monitoring import _classify, revaluate_cold_leads

def test_classify_helper():
    assert _classify(85) == "quente"
    assert _classify(75) == "quente"
    assert _classify(74) == "morno"
    assert _classify(50) == "morno"
    assert _classify(49) == "frio"
    assert _classify(25) == "frio"
    assert _classify(24) == "descarte"
    assert _classify(0) == "descarte"

def test_revaluate_archives_expired_leads():
    """Leads expirados (monitor_until no passado) devem ser arquivados"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.db.base import Base
    from app.models.lead import Lead, LeadPlatform, LeadCategory, LeadStatus

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        # Lead expirado
        expired_lead = Lead(
            username="expired_user",
            platform=LeadPlatform.INSTAGRAM,
            score=30,
            category=LeadCategory.FRIO,
            status=LeadStatus.MONITORING,
            monitor_until=datetime.utcnow() - timedelta(days=1),
        )
        # Lead ainda ativo
        active_lead = Lead(
            username="active_user",
            platform=LeadPlatform.INSTAGRAM,
            score=60,
            category=LeadCategory.MORNO,
            status=LeadStatus.MONITORING,
            monitor_until=datetime.utcnow() + timedelta(days=5),
        )
        db.add_all([expired_lead, active_lead])
        db.commit()

        # Patch SessionLocal para usar nosso db de teste
        with patch("app.tasks.monitoring.SessionLocal") as mock_session:
            mock_session.return_value.__enter__ = lambda s: db
            mock_session.return_value.__exit__ = MagicMock(return_value=False)
            revaluate_cold_leads()

        db.refresh(expired_lead)
        db.refresh(active_lead)
        assert expired_lead.status == LeadStatus.ARCHIVED
        assert active_lead.status == LeadStatus.MONITORING
