from sqlalchemy import Integer, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    keywords: Mapped[list] = mapped_column(JSON, default=lambda: [
        "constelação familiar", "constelação sistêmica",
        "Bert Hellinger", "ordem do amor", "alma família"
    ])
    monitor_days_quente: Mapped[int] = mapped_column(Integer, default=7)
    monitor_days_morno: Mapped[int] = mapped_column(Integer, default=10)
    monitor_days_frio: Mapped[int] = mapped_column(Integer, default=15)
    collect_hour: Mapped[int] = mapped_column(Integer, default=3)
    max_leads_per_day: Mapped[int] = mapped_column(Integer, default=100)
    instagram_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    youtube_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    facebook_enrichment: Mapped[bool] = mapped_column(Boolean, default=True)
    linkedin_enrichment: Mapped[bool] = mapped_column(Boolean, default=False)
