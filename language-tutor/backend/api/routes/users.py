from fastapi import APIRouter, Depends

from api.deps import get_current_user
from api.schemas import UserResponse
from database.models import User

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
