import asyncio
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.patient_generator import PatientGenerator
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_schema import PatientDTO, EarDTO, AudiogramPointDTO
from app.models.enums import EarSideEnum, TestTypeEnum, PatientSourceEnum

async def test_scientific_gen():
    print("Testing Scientific Patient Generator (EBPS)...")
    db = MagicMock(spec=AsyncSession)

    # 1. Mock Database with a "REAL" patient (Asymmetrical Loss)
    real_patient = PatientDTO(
        id=99,
        source_type=PatientSourceEnum.REAL,
        ears=[
            EarDTO(side=EarSideEnum.LEFT, audiogram_points=[
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=1000, threshold_db=10.0),
                AudiogramPointDTO(test_type=TestTypeEnum.BC, frequency=1000, threshold_db=10.0)
            ]),
            EarDTO(side=EarSideEnum.RIGHT, audiogram_points=[
                AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=1000, threshold_db=60.0), # Severe loss
                AudiogramPointDTO(test_type=TestTypeEnum.BC, frequency=1000, threshold_db=10.0)  # Conductive gap
            ])
        ]
    )

    async def mock_get_profiles_by_source(db, source):
        if source == PatientSourceEnum.REAL:
            return [real_patient]
        return []

    async def mock_save_patient(db, dto):
        dto.id = 100
        return dto

    PatientRepository.get_profiles_by_source = mock_get_profiles_by_source
    PatientRepository.save_patient = mock_save_patient

    # 2. Generate a new synthetic patient
    patient_id = await PatientGenerator.generate_patient(db)
    print(f"Generated patient ID: {patient_id}")

    # Manually trigger perturbation logic for inspection
    gen_patient = await PatientGenerator._perturb_real_patient(real_patient)
    PatientGenerator._apply_masking_requirements(gen_patient)

    right_ear = next(e for e in gen_patient.ears if e.side == EarSideEnum.RIGHT)
    left_ear = next(e for e in gen_patient.ears if e.side == EarSideEnum.LEFT)

    print(f"\nRight Ear AC: {[p.threshold_db for p in right_ear.audiogram_points if p.test_type == TestTypeEnum.AC]}")
    print(f"Right Ear BC: {[p.threshold_db for p in right_ear.audiogram_points if p.test_type == TestTypeEnum.BC]}")

    # Verify Clinical Constraints
    for ear in gen_patient.ears:
        for bc_p in [p for p in ear.audiogram_points if p.test_type == TestTypeEnum.BC]:
            ac_p = next(p for p in ear.audiogram_points if p.test_type == TestTypeEnum.AC and p.frequency == bc_p.frequency)
            # BC cannot be significantly worse than AC
            assert bc_p.threshold_db <= ac_p.threshold_db + 5.0
            print(f"Constraint Check Passed for {ear.side} at {bc_p.frequency}Hz: BC({bc_p.threshold_db}) <= AC({ac_p.threshold_db}) + 5")

    # Verify Masking Logic
    # Right Ear AC (60dB) - Left Ear BC (10dB) = 50dB >= 40dB -> Should have AC_MASKED in Right Ear
    has_ac_masked = any(p.test_type == TestTypeEnum.AC_MASKED for p in right_ear.audiogram_points)
    print(f"AC Masking Triggered for Right Ear: {has_ac_masked}")
    assert has_ac_masked

    # Right Ear ABG (60-10 = 50dB) > 10dB -> Should have BC_MASKED in Right Ear
    has_bc_masked = any(p.test_type == TestTypeEnum.BC_MASKED for p in right_ear.audiogram_points)
    print(f"BC Masking Triggered for Right Ear: {has_bc_masked}")
    assert has_bc_masked

    print("\nSuccess! EBPS Generator maintains clinical logic and joint distributions.")

if __name__ == "__main__":
    asyncio.run(test_scientific_gen())
