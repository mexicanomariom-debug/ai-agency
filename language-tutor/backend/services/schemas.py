from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    persona_slug: str | None = None


class ChatMessageSchema(BaseModel):
    role: str
    content: str


class StreamChunk(BaseModel):
    content: str
    done: bool = False


class PersonaSchema(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    avatar_url: str | None
    language: str | None

    model_config = {"from_attributes": True}


class UserSchema(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    language: str | None
    level: str | None
    is_onboarded: bool
    subscription_tier: str

    model_config = {"from_attributes": True}


class CognitiveProfileSchema(BaseModel):
    strengths: str | None
    weaknesses: str | None
    learning_style: str | None
    vocabulary_level: str | None
    grammar_notes: str | None

    model_config = {"from_attributes": True}
