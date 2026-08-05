from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.enums import Language, ProficiencyLevel
from database.grade_mapping import LEVEL_TO_GRADES
from database.models import KnowledgeChunk
from services.openai_service import openai_service


class RAGService:
    async def search(
        self,
        session: AsyncSession,
        query: str,
        language: Language,
        level: ProficiencyLevel,
        limit: int = 5,
    ) -> list[KnowledgeChunk]:
        embedding = await openai_service.create_embedding(query)
        grades = LEVEL_TO_GRADES.get(level, [])

        stmt = select(KnowledgeChunk).where(KnowledgeChunk.language == language)

        if grades:
            stmt = stmt.where(
                (KnowledgeChunk.grade.in_(grades)) | (KnowledgeChunk.grade.is_(None))
            )
        else:
            stmt = stmt.where(KnowledgeChunk.level == level)

        if embedding:
            stmt = (
                stmt.where(KnowledgeChunk.embedding.isnot(None))
                .order_by(KnowledgeChunk.embedding.cosine_distance(embedding))
            )
        else:
            stmt = stmt.order_by(KnowledgeChunk.grade.asc().nulls_last(), KnowledgeChunk.id.asc())

        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def format_context(self, chunks: list[KnowledgeChunk]) -> str:
        if not chunks:
            return ""
        parts = [f"[{chunk.topic}]\n{chunk.content}" for chunk in chunks]
        return "\n\n".join(parts)


rag_service = RAGService()
