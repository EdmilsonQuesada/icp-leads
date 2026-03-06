from datetime import datetime, date
from pydantic import BaseModel

class LeadOut(BaseModel):
    id: int
    username: str
    platform: str
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    city: str | None = None
    country: str | None = None
    age: int | None = None
    birthdate: date | None = None
    birthdate_source: str | None = None
    followers: int | None = None
    score: int
    score_engagement: int = 0
    score_intention: int = 0
    score_profile: int = 0
    category: str
    status: str
    profile_url: str | None = None
    created_at: datetime
    last_monitored_at: datetime | None = None
    contacted_at: datetime | None = None

    class Config:
        from_attributes = True

class LeadList(BaseModel):
    total: int
    items: list[LeadOut]

class SearchJobCreate(BaseModel):
    keywords: list[str]
    platforms: list[str] = ["instagram", "youtube"]
