from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from api.schemas import PersonaResponse
from database.enums import Language
from services.personas import persona_service

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("", response_model=list[PersonaResponse])
async def list_personas(
    language: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
) -> list[PersonaResponse]:
    lang_filter = Language(language) if language else None
    personas = await persona_service.list_active(session, language=lang_filter)
    return [PersonaResponse.model_validate(p) for p in personas]


@router.get("/{slug}", response_model=PersonaResponse)
async def get_persona(slug: str, session: AsyncSession = Depends(get_db)) -> PersonaResponse:
    persona = await persona_service.get_by_slug(session, slug)
    if not persona:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Persona not found")
    return PersonaResponse.model_validate(persona)
