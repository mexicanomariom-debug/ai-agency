from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_whisper_model: str = "whisper-1"
    default_timezone: str = "Europe/Moscow"
    database_url: str = "sqlite+aiosqlite:///./data/agent.db"
    scheduler_database_url: str = "sqlite:///./data/scheduler.db"
    tts_voice: str = "ru-RU-DmitryNeural"
    environment: str = "development"

    # Google Calendar OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8080/oauth/google/callback"
    oauth_server_port: int = 8080

    # Twilio phone calls
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_google_calendar(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def has_twilio(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_from_number)


settings = Settings()
