import logging
from datetime import datetime, timedelta
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.lead import Lead, LeadStatus, LeadCategory, LeadGender
from app.models.lead_event import LeadEvent
from app.services.scorer import LeadScorer
from app.services.gender_detector import detect_gender

logger = logging.getLogger(__name__)

MONITOR_DAYS = {"quente": 7, "morno": 10, "frio": 15, "descarte": 0}


@celery_app.task
def enrich_lead(lead_id: int):
    """Enriquece um lead recém-descoberto."""
    with SessionLocal() as db:
        lead = db.get(Lead, lead_id)
        if not lead:
            return

        lead.status = LeadStatus.ENRICHING
        db.commit()

        # Score inicial com dados disponíveis
        scorer = LeadScorer()
        # Para leads do YouTube, o bio contém o texto do comentário
        comments = [{"text": lead.bio}] if lead.bio else []
        # Força descarte para comentários negativos
        if lead.bio and scorer._is_negative(lead.bio):
            lead.score = 0
            lead.score_engagement = 0
            lead.score_intention = 0
            lead.score_profile = 0
            lead.category = LeadCategory.DESCARTE
            lead.status = LeadStatus.ARCHIVED
            db.add(LeadEvent(
                lead_id=lead.id,
                event_type="enriched",
                description="Comentário negativo detectado. Lead descartado.",
                score_delta=0,
                score_after=0,
            ))
            db.commit()
            logger.info(f"Lead {lead.username} descartado por comentário negativo")
            return

        result = scorer.score({
            "bio": lead.bio or "",
            "country": lead.country or "BR",
            "is_business": lead.is_business_account,
            "followers": lead.followers or 0,
            "engagement_events": [],
            "comments": comments,
        })

        lead.score = result.total
        lead.score_engagement = result.engagement_score
        lead.score_intention = result.intention_score
        lead.score_profile = result.profile_score
        lead.category = LeadCategory(result.category)
        lead.status = LeadStatus.MONITORING

        # Detecção de gênero via nome
        if not lead.gender:
            gender_val, confidence = detect_gender(lead.display_name or lead.username)
            lead.gender = LeadGender(gender_val)
            lead.gender_confidence = confidence

        days = MONITOR_DAYS.get(result.category, 15)
        if days > 0:
            lead.monitor_until = datetime.utcnow() + timedelta(days=days)

        db.add(LeadEvent(
            lead_id=lead.id,
            event_type="enriched",
            description=f"Perfil enriquecido. Score inicial: {result.total}",
            score_delta=result.total,
            score_after=result.total,
        ))
        db.commit()
        logger.info(f"Lead {lead.username} enriquecido: score={result.total}, categoria={result.category}")


@celery_app.task
def process_pending_queue():
    """Processa leads com status PENDING."""
    with SessionLocal() as db:
        pending = db.query(Lead).filter(Lead.status == LeadStatus.PENDING).limit(50).all()
        for lead in pending:
            enrich_lead.delay(lead.id)
        logger.info(f"Enfileirados {len(pending)} leads para enriquecimento")
