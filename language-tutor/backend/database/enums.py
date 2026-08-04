from enum import StrEnum


class Language(StrEnum):
    ENGLISH = "english"
    SPANISH = "spanish"
    FRENCH = "french"
    GERMAN = "german"
    ITALIAN = "italian"
    PORTUGUESE = "portuguese"
    RUSSIAN = "russian"
    JAPANESE = "japanese"
    KOREAN = "korean"
    CHINESE = "chinese"


class ProficiencyLevel(StrEnum):
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    NATIVE = "native"


class SubscriptionTier(StrEnum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
