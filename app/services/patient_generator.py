from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_schema import PatientDTO, EarDTO, AudiogramPointDTO
from app.models.enums import EarSideEnum, TestTypeEnum


class PatientGenerator:

    @staticmethod
    async def generate_patient(db: AsyncSession) -> int | None:

        profiles = await PatientRepository.get_profiles(db)

        if not profiles:
            return None

        def build_default_points() -> list[AudiogramPointDTO]:
            return [
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=250, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=500, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=750, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=1000, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=1500, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=2000, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=3000, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=4000, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=6000, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=8000, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.BC, frequency=500, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.BC, frequency=750, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.BC, frequency=1000, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.BC, frequency=1500, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.BC, frequency=2000, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.BC, frequency=3000, threshold_db=0.0),
                AudiogramPointDTO(test_type=TestTypeEnum.BC, frequency=4000, threshold_db=0.0),
            ]

        left_ear = EarDTO(
            side=EarSideEnum.LEFT,
            audiogram_points=build_default_points()
        )

        right_ear = EarDTO(
            side=EarSideEnum.RIGHT,
            audiogram_points=build_default_points()
        )

        new_patient = PatientDTO(ears=[left_ear, right_ear])
        saved_patient = await PatientRepository.save_patient(db, new_patient)
        return saved_patient.id
# 