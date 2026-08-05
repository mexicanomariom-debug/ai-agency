from fastapi import APIRouter, Depends

from api.deps import get_current_user, get_db
from api.schemas import ProgressResponse, SessionBriefResponse, UserResponse
from database.models import User
from services.progress_service import progress_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        language=user.language.value if user.language else None,
        level=user.level.value if user.level else None,
        audience=user.audience.value if user.audience else None,
        is_onboarded=user.is_onboarded,
        subscription_tier=user.subscription_tier.value if user.subscription_tier else "free",
    )


@router.get("/me/progress", response_model=ProgressResponse)
async def get_my_progress(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProgressResponse:
    snapshot = await progress_service.get_snapshot(session, user)
    return ProgressResponse(
        profile_level=snapshot.profile_level,
        speaking_cefr=snapshot.speaking_cefr,
        target_language=snapshot.target_language,
        last_session_summary=snapshot.last_session_summary,
        last_assessed_at=snapshot.last_assessed_at,
        vocab_total=snapshot.vocab_total,
        vocab_due=snapshot.vocab_due,
        vocab_mastered=snapshot.vocab_mastered,
        sessions_count=snapshot.sessions_count,
        messages_count=snapshot.messages_count,
        streak_days=snapshot.streak_days,
        strengths=snapshot.strengths,
        weaknesses=snapshot.weaknesses,
        recommendation=snapshot.recommendation,
        recent_sessions=[
            SessionBriefResponse(
                date=s.date,
                speaking_cefr=s.speaking_cefr,
                summary=s.summary,
                recommendation=s.recommendation,
            )
            for s in snapshot.recent_sessions
        ],
    )
