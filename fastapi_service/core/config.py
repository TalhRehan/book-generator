"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    openai_api_key: str

    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    notify_email: str

    teams_webhook_url: str
    app_env: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()