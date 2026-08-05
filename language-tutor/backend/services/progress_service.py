from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import ChatMessage, CognitiveProfile, SessionAssessment, User, VocabularyCard
from services.cognitive_profiler import cognitive_profiler
from services.vocabulary_service import vocabulary_service


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_bullets(text: str | None, limit: int = 5) -> list[str]:
    if not text:
        return []
    items: list[str] = []
    for line in text.split("\n"):
        line = line.strip().lstrip("-• ").strip()
        if line and line not in items:
            items.append(line)
    return items[:limit]


def _activity_dates(
    assessment_days: list[date],
    message_days: list[date],
) -> set[date]:
    return set(assessment_days) | set(message_days)


def _streak_from_dates(days: set[date], today: date) -> int:
    if not days:
        return 0
    streak = 0
    cursor = today
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


@dataclass
class SessionBrief:
    date: str
    speaking_cefr: str | None
    summary: str | None
    recommendation: str | None


@dataclass
class ProgressSnapshot:
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
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendation: str | None = None
    recent_sessions: list[SessionBrief] = field(default_factory=list)


class ProgressService:
    async def get_snapshot(self, session: AsyncSession, user: User) -> ProgressSnapshot:
        if not user.cognitive_profile:
            result = await session.execute(
                select(User)
                .options(selectinload(User.cognitive_profile))
                .where(User.id == user.id)
            )
            user = result.scalar_one_or_none() or user

        profile: CognitiveProfile | None = user.cognitive_profile
        if not profile:
            profile = await cognitive_profiler.get_or_create(session, user)

        now = _utc_now()
        today = now.date()

        vocab_total = await vocabulary_service.count_total(session, user)
        vocab_due = await vocabulary_service.count_due(session, user)

        mastered_stmt = (
            select(func.count())
            .select_from(VocabularyCard)
            .where(VocabularyCard.user_id == user.id, VocabularyCard.reps >= 3)
        )
        vocab_mastered = int((await session.execute(mastered_stmt)).scalar_one())

        sessions_count_stmt = (
            select(func.count())
            .select_from(SessionAssessment)
            .where(SessionAssessment.user_id == user.id)
        )
        sessions_count = int((await session.execute(sessions_count_stmt)).scalar_one())

        messages_count_stmt = (
            select(func.count())
            .select_from(ChatMessage)
            .where(ChatMessage.user_id == user.id)
        )
        messages_count = int((await session.execute(messages_count_stmt)).scalar_one())

        assessment_days_stmt = (
            select(func.date_trunc("day", SessionAssessment.created_at))
            .where(SessionAssessment.user_id == user.id)
        )
        assessment_days = [
            row[0].date() if hasattr(row[0], "date") else row[0]
            for row in (await session.execute(assessment_days_stmt)).all()
        ]

        message_days_stmt = (
            select(func.date_trunc("day", ChatMessage.created_at))
            .where(ChatMessage.user_id == user.id)
        )
        message_days = [
            row[0].date() if hasattr(row[0], "date") else row[0]
            for row in (await session.execute(message_days_stmt)).all()
        ]

        streak_days = _streak_from_dates(
            _activity_dates(assessment_days, message_days),
            today,
        )

        recent_stmt = (
            select(SessionAssessment)
            .where(SessionAssessment.user_id == user.id)
            .order_by(SessionAssessment.created_at.desc())
            .limit(3)
        )
        recent_rows = (await session.execute(recent_stmt)).scalars().all()
        recent_sessions = [
            SessionBrief(
                date=row.created_at.strftime("%d.%m.%Y"),
                speaking_cefr=row.speaking_cefr,
                summary=(row.summary or "")[:300] or None,
                recommendation=(row.recommendation or "")[:200] or None,
            )
            for row in recent_rows
        ]

        last_assessment = recent_rows[0] if recent_rows else None
        recommendation = None
        if last_assessment and last_assessment.recommendation:
            recommendation = last_assessment.recommendation.strip()
        elif profile.grammar_notes:
            for line in profile.grammar_notes.split("\n"):
                if line.strip().lower().startswith("next:"):
                    recommendation = line.split(":", 1)[-1].strip()
                    break

        last_assessed_at = None
        if profile.last_assessed_at:
            last_assessed_at = profile.last_assessed_at.isoformat()

        return ProgressSnapshot(
            profile_level=user.level.value if user.level else None,
            speaking_cefr=profile.last_speaking_cefr,
            target_language=user.language.value if user.language else None,
            last_session_summary=profile.last_session_summary,
            last_assessed_at=last_assessed_at,
            vocab_total=vocab_total,
            vocab_due=vocab_due,
            vocab_mastered=vocab_mastered,
            sessions_count=sessions_count,
            messages_count=messages_count,
            streak_days=streak_days,
            strengths=_parse_bullets(profile.strengths),
            weaknesses=_parse_bullets(profile.weaknesses),
            recommendation=recommendation,
            recent_sessions=recent_sessions,
        )

    def format_telegram(self, snapshot: ProgressSnapshot) -> str:
        lang = snapshot.target_language or "—"
        level = snapshot.profile_level or "не задан"
        cefr = snapshot.speaking_cefr or "ещё не оценён"

        lines = [
            "📊 <b>Ваш прогресс</b>",
            "",
            f"🌍 Язык: <b>{lang}</b>",
            f"📈 Уровень профиля: <b>{level}</b>",
            f"🎙 Речь (CEFR): <b>{cefr}</b>",
            "",
            f"🔥 Серия: <b>{snapshot.streak_days}</b> дн.",
            f"💬 Сообщений в чате: <b>{snapshot.messages_count}</b>",
            f"🎓 Оценённых уроков: <b>{snapshot.sessions_count}</b>",
            "",
            f"📚 Словарь: <b>{snapshot.vocab_total}</b> слов",
            f"   · на сегодня: <b>{snapshot.vocab_due}</b>",
            f"   · в памяти (3+ повторений): <b>{snapshot.vocab_mastered}</b>",
        ]

        if snapshot.last_session_summary:
            lines.extend(["", "📝 Последний урок:", snapshot.last_session_summary[:500]])

        if snapshot.strengths:
            lines.extend(["", "✅ Сильные стороны:"])
            for item in snapshot.strengths[:4]:
                lines.append(f"• {item}")

        if snapshot.weaknesses:
            lines.extend(["", "🎯 Работаем на:"])
            for item in snapshot.weaknesses[:4]:
                lines.append(f"• {item}")

        if snapshot.recommendation:
            lines.extend(["", f"💡 Совет: {snapshot.recommendation[:400]}"])

        if snapshot.recent_sessions:
            lines.extend(["", "📅 Недавние уроки:"])
            for sess in snapshot.recent_sessions:
                cefr_tag = f" ({sess.speaking_cefr})" if sess.speaking_cefr else ""
                lines.append(f"• {sess.date}{cefr_tag}")
                if sess.summary:
                    short = sess.summary[:120]
                    if len(sess.summary) > 120:
                        short += "…"
                    lines.append(f"  {short}")

        if snapshot.vocab_due > 0:
            lines.extend(["", "👉 /review — повторить слова на сегодня"])

        return "\n".join(lines)


progress_service = ProgressService()
