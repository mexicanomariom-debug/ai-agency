from fastapi import APIRouter, Depends

from api.deps import get_current_user
from api.schemas import UserResponse
from database.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)
