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
    audience: str | None = None
    is_onboarded: bool
    subscription_tier: str

    model_config = {"from_attributes": True}


class VoiceTalkResponse(BaseModel):
    transcript: str
    reply: str
    audio_base64: str | None = None
    audio_mime: str | None = None
    error: str | None = None


class VoiceChatRequest(BaseModel):
    message: str
    persona_slug: str | None = None


class VoiceCapabilitiesResponse(BaseModel):
    llm: bool
    stt: bool
    tts: bool
    provider: str | None = None
    chat_model: str | None = None


class VoiceTutorResponse(BaseModel):
    name: str
    slug: str
    description: str
    language: str | None
    level: str | None
    audience: str | None = None
    greeting: str


class VoiceSessionCloseRequest(BaseModel):
    persona_slug: str | None = None


class VoiceSessionAssessmentResponse(BaseModel):
    assessed: bool
    skipped_reason: str | None = None
    speaking_cefr: str | None = None
    mapped_level: str | None = None
    confidence: str | None = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    grammar_focus: list[str] = []
    recommendation: str | None = None
    summary: str | None = None
    level_updated: bool = False
    words_added: int = 0


class MessageResponse(BaseModel):
    role: str
    content: str
    created_at: str

    model_config = {"from_attributes": True}


class SessionBriefResponse(BaseModel):
    date: str
    speaking_cefr: str | None = None
    summary: str | None = None
    recommendation: str | None = None


class ProgressResponse(BaseModel):
    profile_level: str | None = None
    speaking_cefr: str | None = None
    target_language: str | None = None
    last_session_summary: str | None = None
    last_assessed_at: str | None = None
    vocab_total: int = 0
    vocab_due: int = 0
    vocab_mastered: int = 0
    sessions_count: int = 0
    messages_count: int = 0
    streak_days: int = 0
    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendation: str | None = None
    recent_sessions: list[SessionBriefResponse] = []
