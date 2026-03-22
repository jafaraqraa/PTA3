from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.session_repository import SessionRepository
from app.repositories.attempt_repository import AttemptRepository
from app.repositories.stored_threshold_repository import StoredThresholdRepository

from app.schemas.attempt_schema import  AttemptCreateDTO
from app.schemas.stored_threshold_schema import CreateStoredThresholdDTO, StoredThresholdDTO
from app.schemas.session_schema import SessionCreateDTO, SessionDTO, SessionFullDTO, SessionWithPatientDTO
from app.services.evaluation_engine import EvaluationEngine
from app.services.response_engine import ResponseEngine
from app.services.patient_generator import PatientGenerator


class SessionManager:

    @staticmethod
    async def start_session(db: AsyncSession, user_id: int) -> SessionDTO:

        patient_id = await PatientGenerator.generate_patient(db)

        if not patient_id:
            raise ValueError("No patient profile available")

        return await SessionManager.create_session(
            db,
            user_id,
            patient_id
        )

    @staticmethod
    async def create_session(db: AsyncSession, user_id: int, patient_id: int) -> SessionDTO:

        session_dto = SessionCreateDTO(
            user_id=user_id,
            patient_id=patient_id
        )
        return await SessionRepository.create_session(db, session_dto)
    
    @staticmethod
    async def end_session(db: AsyncSession, session_id: int):

        session: SessionFullDTO | None = await SessionRepository.get_full_session(
            db,
            session_id
        )

        if not session:
            raise ValueError("Session not found")

        results = EvaluationEngine.evaluate_session(session)

        return results

    @staticmethod
    async def store_threshold(db: AsyncSession, dto: CreateStoredThresholdDTO) -> StoredThresholdDTO:

        session = await SessionRepository.get_session(db, dto.session_id)
        if not session:
            raise ValueError("Session not found")
        threshold = await StoredThresholdRepository.store_threshold(db, dto)
        return threshold

    @staticmethod
    async def play_tone(
        db: AsyncSession,
        dto: AttemptCreateDTO
    ):

        # 1️⃣ get session
        session: SessionWithPatientDTO | None = await SessionRepository.get_session_with_patient(
            db,
            dto.session_id
        )

        if not session:
            raise ValueError("Session not found")

        # 2️⃣ get patient
        patient = session.patient
        if not patient:
            raise ValueError("Patient not found")

        # 3️⃣ evaluate tone
        response = ResponseEngine.evaluate_tone(patient, dto)

        # 4️⃣ update dto
        dto.response = response

        # 5️⃣ save attempt
        await AttemptRepository.create_attempt(
            db,
            dto
        )

        return response
