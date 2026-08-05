from enum import Enum as PyEnum

from sqlalchemy import Enum as SAEnum

from database.enums import Audience, Language, MessageRole, ProficiencyLevel, SubscriptionTier


def _values(enum_cls: type[PyEnum]) -> list[str]:
    return [member.value for member in enum_cls]


LanguageEnum = SAEnum(
    Language,
    name="language",
    values_callable=_values,
    create_constraint=True,
)
ProficiencyLevelEnum = SAEnum(
    ProficiencyLevel,
    name="proficiencylevel",
    values_callable=_values,
    create_constraint=True,
)
AudienceEnum = SAEnum(
    Audience,
    name="audience",
    values_callable=_values,
    create_constraint=True,
)
SubscriptionTierEnum = SAEnum(
    SubscriptionTier,
    name="subscriptiontier",
    values_callable=_values,
    create_constraint=True,
)
MessageRoleEnum = SAEnum(
    MessageRole,
    name="messagerole",
    values_callable=_values,
    create_constraint=True,
)
