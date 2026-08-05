from pydantic import BaseModel


class ChatStreamRequest(BaseModel):
    message: str
    persona_slug: str | None = None


class PersonaResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    avatar_url: str | None
    language: str | None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    language: str | None
    level: str | None
    is_onboarded: bool
    subscription_tier: str

    model_config = {"from_attributes": True}


class VoiceTalkResponse(BaseModel):
    transcript: str
    reply: str
    audio_base64: str | None = None
    audio_mime: str | None = None
    error: str | None = None


class VoiceTutorResponse(BaseModel):
    name: str
    slug: str
    description: str
    language: str | None
    level: str | None
    greeting: str


class MessageResponse(BaseModel):
    role: str
    content: str
    created_at: str

    model_config = {"from_attributes": True}
