from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class SearchJob(Base):
    __tablename__ = "search_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keywords: Mapped[list] = mapped_column(JSON)
    platforms: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    leads_found: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
