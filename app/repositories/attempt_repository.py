from sqlalchemy.ext.asyncio import AsyncSession
from app.models.attempt import Attempt
from app.schemas.attempt_schema import AttemptDTO, AttemptCreateDTO


class AttemptRepository:

    @staticmethod
    async def create_attempt(db: AsyncSession, dto: AttemptCreateDTO) -> AttemptDTO:

        attempt = Attempt(
            session_id=dto.session_id,
            ear_side=dto.ear_side,
            test_type=dto.test_type,
            frequency=dto.frequency,
            intensity=dto.intensity,
            masking_level_db=dto.masking_level_db,
            response=dto.response
        )

        db.add(attempt)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        await db.refresh(attempt)

        return AttemptDTO.model_validate(attempt)
