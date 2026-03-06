import logging
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.lead import Lead, LeadStatus, LeadCategory
from app.models.lead_event import LeadEvent

logger = logging.getLogger(__name__)


def _classify(score: int) -> str:
    if score >= 75:
        return "quente"
    elif score >= 50:
        return "morno"
    elif score >= 25:
        return "frio"
    return "descarte"


@celery_app.task
def run_daily_monitoring():
    """Dispara monitoramento para todos os leads ativos."""
    with SessionLocal() as db:
        active = db.query(Lead).filter(
            Lead.status == LeadStatus.MONITORING,
            Lead.monitor_until >= datetime.utcnow(),
        ).all()
        for lead in active:
            monitor_lead.delay(lead.id)
        logger.info(f"Monitoramento iniciado para {len(active)} leads")


@celery_app.task
def monitor_lead(lead_id: int):
    """Verifica atividade recente de um lead e atualiza score."""
    with SessionLocal() as db:
        lead = db.get(Lead, lead_id)
        if not lead:
            return

        lead.monitoring_days += 1
        lead.last_monitored_at = datetime.utcnow()
        score_delta = 0
        events_to_add = []

        # Verifica aniversário próximo (dentro de 7 dias)
        if lead.birthdate:
            from datetime import date, timedelta
            today = date.today()
            try:
                bday_this_year = lead.birthdate.replace(year=today.year)
                days_until = (bday_this_year - today).days
                if 0 <= days_until <= 7:
                    events_to_add.append(LeadEvent(
                        lead_id=lead.id,
                        event_type="birthday_soon",
                        description=f"Aniversário em {days_until} dias",
                        score_delta=0,
                        score_after=lead.score,
                    ))
            except ValueError:
                pass

        # Penalidade por inatividade
        if lead.monitoring_days > 7 and not events_to_add:
            score_delta = -10

        if score_delta != 0:
            old_score = lead.score
            lead.score = max(0, lead.score + score_delta)
            new_category = _classify(lead.score)
            if new_category != lead.category.value:
                events_to_add.append(LeadEvent(
                    lead_id=lead.id,
                    event_type="score_change",
                    description=f"Categoria: {lead.category.value} → {new_category}",
                    score_delta=score_delta,
                    score_after=lead.score,
                ))
                lead.category = LeadCategory(new_category)

        for event in events_to_add:
            db.add(event)
        db.commit()


@celery_app.task
def revaluate_cold_leads():
    """Arquiva leads cujo período de monitoramento expirou."""
    with SessionLocal() as db:
        expired = db.query(Lead).filter(
            Lead.status == LeadStatus.MONITORING,
            Lead.monitor_until < datetime.utcnow(),
        ).all()
        for lead in expired:
            lead.status = LeadStatus.ARCHIVED
        db.commit()
        logger.info(f"Arquivados {len(expired)} leads expirados")
