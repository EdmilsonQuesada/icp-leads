import enum
from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Enum, Text, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class LeadPlatform(str, enum.Enum):
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"

class LeadGender(str, enum.Enum):
    F = "F"
    M = "M"
    ND = "ND"

class LeadCategory(str, enum.Enum):
    QUENTE = "quente"
    MORNO = "morno"
    FRIO = "frio"
    DESCARTE = "descarte"

class LeadStatus(str, enum.Enum):
    PENDING = "pending"
    ENRICHING = "enriching"
    MONITORING = "monitoring"
    READY = "ready"
    CONTACTED = "contacted"
    ARCHIVED = "archived"

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), index=True)
    platform: Mapped[LeadPlatform] = mapped_column(Enum(LeadPlatform))
    display_name: Mapped[str | None] = mapped_column(String(200))
    bio: Mapped[str | None] = mapped_column(Text)
    profile_url: Mapped[str | None] = mapped_column(String(500))
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100), default="BR")
    age: Mapped[int | None] = mapped_column(Integer)
    birthdate: Mapped[date | None] = mapped_column(Date)
    birthdate_source: Mapped[str | None] = mapped_column(String(50))

    followers: Mapped[int | None] = mapped_column(Integer)
    following: Mapped[int | None] = mapped_column(Integer)
    is_business_account: Mapped[bool] = mapped_column(Boolean, default=False)

    gender: Mapped[LeadGender | None] = mapped_column(Enum(LeadGender), nullable=True)
    gender_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    message_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    creator_profile: Mapped[str | None] = mapped_column(String(200), nullable=True)

    score: Mapped[int] = mapped_column(Integer, default=0)
    score_engagement: Mapped[int] = mapped_column(Integer, default=0)
    score_intention: Mapped[int] = mapped_column(Integer, default=0)
    score_profile: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[LeadCategory] = mapped_column(Enum(LeadCategory), default=LeadCategory.FRIO)
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.PENDING)

    monitor_until: Mapped[datetime | None] = mapped_column(DateTime)
    monitoring_days: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_monitored_at: Mapped[datetime | None] = mapped_column(DateTime)
    contacted_at: Mapped[datetime | None] = mapped_column(DateTime)

    events: Mapped[list["LeadEvent"]] = relationship(back_populates="lead",
                                                       order_by="LeadEvent.created_at")
