from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.enums import Audience, Language, ProficiencyLevel, SubscriptionTier
from database.models import User


class UserService:
    async def get_by_telegram_id(self, session: AsyncSession, telegram_id: int) -> User | None:
        result = await session.execute(
            select(User)
            .options(selectinload(User.cognitive_profile))
            .where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        user = await self.get_by_telegram_id(session, telegram_id)
        if user:
            user.username = username or user.username
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            return user

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)
        await session.flush()
        return user

    async def set_audience(self, session: AsyncSession, user: User, audience: Audience) -> User:
        user.audience = audience
        await session.flush()
        return user

    async def set_language(self, session: AsyncSession, user: User, language: Language) -> User:
        user.language = language
        await session.flush()
        return user

    async def set_level(self, session: AsyncSession, user: User, level: ProficiencyLevel) -> User:
        user.level = level
        await session.flush()
        return user

    async def complete_onboarding(self, session: AsyncSession, user: User) -> User:
        user.is_onboarded = True
        await session.flush()
        return user

    async def set_subscription(
        self, session: AsyncSession, user: User, tier: SubscriptionTier, stripe_customer_id: str | None = None
    ) -> User:
        user.subscription_tier = tier
        if stripe_customer_id:
            user.stripe_customer_id = stripe_customer_id
        await session.flush()
        return user


user_service = UserService()
