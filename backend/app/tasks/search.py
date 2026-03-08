import logging
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.search_job import SearchJob
from app.models.lead import Lead, LeadPlatform, LeadStatus

logger = logging.getLogger(__name__)


def _lead_exists(db, username: str, platform: LeadPlatform) -> bool:
    return db.query(Lead).filter(
        Lead.username == username,
        Lead.platform == platform,
    ).first() is not None


def _create_lead(db, data: dict, platform: LeadPlatform) -> Lead | None:
    username = data.get("username") or data.get("channel_id")
    if not username:
        return None
    if _lead_exists(db, username, platform):
        return None

    lead = Lead(
        username=username,
        platform=platform,
        display_name=data.get("display_name") or data.get("username"),
        bio=data.get("bio") or data.get("post_text") or data.get("text"),
        followers=data.get("followers"),
        following=data.get("following"),
        is_business_account=data.get("is_business", False),
        profile_url=data.get("profile_url"),
        avatar_url=data.get("avatar_url"),
        status=LeadStatus.PENDING,
    )
    db.add(lead)
    db.flush()
    return lead


def _run_instagram(keywords: list[str]) -> list[dict]:
    from app.collectors.instagram import InstagramCollector
    leads_data = []
    try:
        collector = InstagramCollector()
        MAX_POSTS_PER_HASHTAG = 22
        MAX_PROFILES_PER_HASHTAG = 15
        for keyword in keywords:
            hashtag = keyword.lstrip("#")
            posts = collector.search_hashtag(hashtag, limit=MAX_POSTS_PER_HASHTAG)
            seen_usernames = set()
            for post in posts:
                if len(seen_usernames) >= MAX_PROFILES_PER_HASHTAG:
                    break
                uname = post.get("username")
                if uname and uname not in seen_usernames:
                    seen_usernames.add(uname)
                    try:
                        profile = collector.get_profile(uname)
                        profile["post_text"] = post.get("post_text", "")
                        profile["profile_url"] = f"https://instagram.com/{uname}"
                        leads_data.append(profile)
                    except Exception as e:
                        logger.warning(f"Falha ao buscar perfil @{uname}: {e}")
    except Exception as e:
        logger.error(f"Erro no coletor Instagram: {e}")
    return leads_data


def _run_youtube(keywords: list[str]) -> list[dict]:
    from app.collectors.youtube import YouTubeCollector
    leads_data = []
    try:
        collector = YouTubeCollector()
        for keyword in keywords:
            videos = collector.search_videos(keyword, max_results=8)
            for video in videos:
                video_id = video["video_id"]
                try:
                    comments = collector.get_comments(video_id, max_results=38)
                    for c in comments:
                        channel_id = c.get("channel_id")
                        if not channel_id:
                            continue
                        leads_data.append({
                            "username": channel_id,
                            "display_name": c.get("username"),
                            "bio": c.get("text"),
                            "profile_url": f"https://youtube.com/channel/{channel_id}",
                        })
                except Exception as e:
                    logger.warning(f"Falha ao buscar comentários de {video_id}: {e}")
    except Exception as e:
        logger.error(f"Erro no coletor YouTube: {e}")
    return leads_data


@celery_app.task(bind=True, max_retries=0)
def run_search_job(self, job_id: int):
    """Executa um SearchJob: coleta leads nas plataformas e cria registros."""
    from app.tasks.enrichment import enrich_lead

    with SessionLocal() as db:
        job = db.get(SearchJob, job_id)
        if not job:
            logger.error(f"SearchJob {job_id} não encontrado")
            return

        job.status = "running"
        db.commit()
        logger.info(f"Iniciando job {job_id}: keywords={job.keywords}, platforms={job.platforms}")

    leads_created = 0
    errors = []

    try:
        platforms = job.platforms if isinstance(job.platforms, list) else [job.platforms]
        keywords = job.keywords if isinstance(job.keywords, list) else [job.keywords]

        all_leads: list[tuple[dict, LeadPlatform]] = []

        if "instagram" in platforms:
            for data in _run_instagram(keywords):
                all_leads.append((data, LeadPlatform.INSTAGRAM))

        if "youtube" in platforms:
            for data in _run_youtube(keywords):
                all_leads.append((data, LeadPlatform.YOUTUBE))

        with SessionLocal() as db:
            new_lead_ids = []
            for data, platform in all_leads:
                lead = _create_lead(db, data, platform)
                if lead:
                    new_lead_ids.append(lead.id)
                    leads_created += 1

            job = db.get(SearchJob, job_id)
            job.leads_found = leads_created
            job.status = "done"
            job.finished_at = datetime.utcnow()
            db.commit()

        for lead_id in new_lead_ids:
            enrich_lead.delay(lead_id)

        logger.info(f"Job {job_id} concluído: {leads_created} leads criados")

    except Exception as e:
        logger.error(f"Job {job_id} falhou: {e}", exc_info=True)
        with SessionLocal() as db:
            job = db.get(SearchJob, job_id)
            if job:
                job.status = "error"
                job.error_message = str(e)
                job.finished_at = datetime.utcnow()
                db.commit()
