from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.patient import Patient, Ear, AudiogramPoint
from app.schemas.patient_schema import PatientDTO


class PatientRepository:

    @staticmethod
    async def get_profiles(db: AsyncSession):

        result = await db.execute(select(Patient))

        patients = result.scalars().all()

        return [PatientDTO.model_validate(p) for p in patients]

    @staticmethod
    async def get_profiles_by_source(db: AsyncSession, source_type):

        result = await db.execute(
            select(Patient).where(Patient.source_type == source_type)
        )

        patients = result.scalars().all()

        return [PatientDTO.model_validate(p) for p in patients]

    @staticmethod
    async def save_patient(db: AsyncSession, dto: PatientDTO) -> PatientDTO:

        patient = Patient(
            source_type=dto.source_type
        )

        for ear_dto in dto.ears:
            ear = Ear(
                side=ear_dto.side,
                hearing_type=ear_dto.hearing_type
            )

            for point_dto in ear_dto.audiogram_points:
                point = AudiogramPoint(
                    test_type=point_dto.test_type,
                    frequency=point_dto.frequency,
                    threshold_db=point_dto.threshold_db
                )
                ear.audiogram_points.append(point)

            patient.ears.append(ear)
        db.add(patient)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        await db.refresh(patient)

        return PatientDTO.model_validate(patient)
