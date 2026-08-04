from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = ""
    bot_username: str = "All_languages_bot"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    database_url: str = "postgresql+asyncpg://language_tutor:language_tutor@localhost:5432/language_tutor"
    twa_url: str = "https://webapp-bay-three-75.vercel.app"
    api_url: str = "http://localhost:8000"
    webapp_url: str = "http://localhost:3000"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "change-me-in-production"
    demo_mode: bool = True
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    environment: str = "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
