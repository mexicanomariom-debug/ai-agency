from datetime import datetime, timezone

from fsrs import Card, Rating, Scheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, VocabularyCard

_scheduler = Scheduler()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _card_from_row(row: VocabularyCard) -> Card:
    return Card.from_json(row.fsrs_card_json)


def _rating_from_int(value: int) -> Rating:
    mapping = {
        1: Rating.Again,
        2: Rating.Hard,
        3: Rating.Good,
        4: Rating.Easy,
    }
    return mapping.get(value, Rating.Good)


class VocabularyService:
    async def count_due(self, session: AsyncSession, user: User) -> int:
        now = _utc_now()
        stmt = (
            select(VocabularyCard.id)
            .where(VocabularyCard.user_id == user.id, VocabularyCard.due_at <= now)
        )
        result = await session.execute(stmt)
        return len(result.scalars().all())

    async def count_total(self, session: AsyncSession, user: User) -> int:
        stmt = select(VocabularyCard.id).where(VocabularyCard.user_id == user.id)
        result = await session.execute(stmt)
        return len(result.scalars().all())

    async def get_next_due(self, session: AsyncSession, user: User) -> VocabularyCard | None:
        now = _utc_now()
        stmt = (
            select(VocabularyCard)
            .where(VocabularyCard.user_id == user.id, VocabularyCard.due_at <= now)
            .order_by(VocabularyCard.due_at.asc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_word(
        self,
        session: AsyncSession,
        user: User,
        *,
        word: str,
        translation: str,
        example: str | None = None,
        target_language: str | None = None,
    ) -> VocabularyCard | None:
        word_clean = word.strip()
        translation_clean = translation.strip()
        if not word_clean or not translation_clean:
            return None

        lang = target_language or (user.language.value if user.language else None)

        stmt = select(VocabularyCard).where(
            VocabularyCard.user_id == user.id,
            VocabularyCard.word == word_clean,
            VocabularyCard.target_language == lang,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return None

        fsrs_card = Card()
        now = _utc_now()
        row = VocabularyCard(
            user_id=user.id,
            word=word_clean,
            translation=translation_clean,
            example=(example or "").strip() or None,
            target_language=lang,
            fsrs_card_json=fsrs_card.to_json(),
            due_at=fsrs_card.due or now,
            reps=0,
        )
        session.add(row)
        await session.flush()
        return row

    async def import_words(
        self,
        session: AsyncSession,
        user: User,
        words: list[dict],
    ) -> int:
        added = 0
        lang = user.language.value if user.language else None
        for item in words[:8]:
            word = str(item.get("word", "")).strip()
            translation = str(item.get("translation", "")).strip()
            example = str(item.get("example", "")).strip() or None
            if not word or not translation:
                continue
            row = await self.add_word(
                session,
                user,
                word=word,
                translation=translation,
                example=example,
                target_language=lang,
            )
            if row:
                added += 1
        return added

    async def review(
        self,
        session: AsyncSession,
        card_row: VocabularyCard,
        rating_value: int,
    ) -> VocabularyCard:
        fsrs_card = _card_from_row(card_row)
        rating = _rating_from_int(rating_value)
        fsrs_card, _ = _scheduler.review_card(fsrs_card, rating, review_datetime=_utc_now())
        card_row.fsrs_card_json = fsrs_card.to_json()
        card_row.due_at = fsrs_card.due or _utc_now()
        card_row.reps = (card_row.reps or 0) + 1
        await session.flush()
        return card_row


vocabulary_service = VocabularyService()
