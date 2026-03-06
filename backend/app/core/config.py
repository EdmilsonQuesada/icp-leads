from pydantic_settings import BaseSettings

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

    class Config:
        env_file = ".env"

settings = Settings()
