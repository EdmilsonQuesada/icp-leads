from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://icp:icp@db:5432/icp_leads"
    REDIS_URL: str = "redis://redis:6379/0"
    INSTAGRAM_USERNAME: str = ""
    INSTAGRAM_PASSWORD: str = ""
    YOUTUBE_API_KEY: str = ""
    FACEBOOK_EMAIL: str = ""
    FACEBOOK_PASSWORD: str = ""
    LINKEDIN_EMAIL: str = ""
    LINKEDIN_PASSWORD: str = ""
    COLLECT_HOUR: int = 3
    MAX_LEADS_PER_DAY: int = 100
    APIFY_API_TOKEN: str = Field(
        default="",
        description="Apify API token for Instagram scraping"
    )

    class Config:
        env_file = ".env"

settings = Settings()
