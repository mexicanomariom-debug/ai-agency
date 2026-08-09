from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    default_timezone: str = "Europe/Moscow"
    database_url: str = "sqlite+aiosqlite:///./data/agent.db"
    scheduler_database_url: str = "sqlite:///./data/scheduler.db"
    tts_voice: str = "ru-RU-DmitryNeural"
    environment: str = "development"


settings = Settings()
