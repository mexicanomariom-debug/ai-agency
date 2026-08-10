from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    bot_token: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_whisper_model: str = "whisper-1"
    default_timezone: str = "UTC"
    bot_build_id: str = "dev"
    database_url: str = "sqlite+aiosqlite:///./data/agent.db"
    scheduler_database_url: str = "sqlite:///./data/scheduler.db"
    tts_voice: str = "ru-RU-DmitryNeural"
    environment: str = "development"

    # Google Calendar OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "https://ai-agency-drab.vercel.app/api/google/oauth/callback"
    oauth_server_port: int = 8080
    internal_api_secret: str = Field(
        default="",
        validation_alias=AliasChoices(
            "INTERNAL_API_SECRET",
            "PERSONAL_AGENT_INTERNAL_SECRET",
        ),
    )

    # Twilio phone calls
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    google_maps_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "GOOGLE_MAPS_API_KEY",
            "GOOGLE_DIRECTIONS_API_KEY",
        ),
    )

    yandex_maps_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "YANDEX_MAPS_API_KEY",
            "YANDEX_ROUTING_API_KEY",
        ),
    )

    dgis_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "DGIS_API_KEY",
            "TWOGIS_API_KEY",
        ),
    )

    rsshub_base_url: str = Field(
        default="https://rsshub.app",
        validation_alias=AliasChoices("RSSHUB_BASE_URL"),
    )

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_google_calendar(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def has_twilio(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_from_number)

    @property
    def has_google_maps(self) -> bool:
        return bool(self.google_maps_api_key)

    @property
    def has_yandex_maps(self) -> bool:
        return bool(self.yandex_maps_api_key)

    @property
    def has_dgis(self) -> bool:
        return bool(self.dgis_api_key)


settings = Settings()
